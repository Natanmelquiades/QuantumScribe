"""Orquestrador Central da Aplicação LocalWhisper.

Este módulo centraliza todo o ciclo de vida do LocalWhisper. Ele escuta as
ações do usuário (atalhos globais, menu da bandeja e teclado), coordena a
captura de áudio, invoca a transcrição offline da IA em threads dedicadas e
injeta o resultado de texto de volta nos aplicativos ativos.
"""

from __future__ import annotations

import ctypes
import tempfile
import threading
import tkinter as tk
from pathlib import Path

# Remove o logo do Python da barra de tarefas forçando o AppUserModelID exclusivo no Windows
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("natan.quantumscribe.app.2.1")
except Exception:
    pass

from .audio import AudioRecorder
from .config import AppConfig, load_config, save_config
from .diary import save_entry
from .hotkey import EscapeHotkey, GlobalHotkey
from .settings_ui import SettingsWindow, load_or_generate_icon
from .sounds import play_cancel_sound, play_end_sound, play_start_sound
from .transcriber import LocalTranscriber
from .tray import TrayIcon
from .ui import Popup
from .windows import (
    WindowTarget,
    acquire_single_instance,
    capture_input_target,
    press_enter,
    set_clipboard_text,
    type_into_window,
)


class QuantumScribeApp:
    """Classe principal que inicializa os subsistemas e coordena os fluxos de trabalho."""

    def __init__(self) -> None:
        """Inicializa os componentes fundamentais do aplicativo."""
        # Loop do Tkinter oculto para receber mensagens do SO e criar o popup
        self.root = tk.Tk()
        self.root.withdraw()

        # Carrega arquivos de configurações e subsistemas
        self.config = load_config()
        self.recorder = AudioRecorder()

        # Configura o ícone oficial no root do aplicativo
        try:
            self._icon_img = load_or_generate_icon()
            from PIL import ImageTk
            self._icon_photo = ImageTk.PhotoImage(self._icon_img)
            self.root.iconphoto(False, self._icon_photo)
        except Exception:
            pass

        # Cria a interface do popup fornecendo a referência para ler a amplitude em tempo real
        self.popup = Popup(
            self.root,
            self._on_hud_cancel,
            get_amplitude=self.recorder.get_last_amplitude,
            config=self.config
        )
        self.transcriber = LocalTranscriber(self.config, self._threadsafe_status)
        self.target_window = WindowTarget(0)
        self.processing = False
        self.starting = False
        self._transcription_thread: threading.Thread | None = None

        # Estado ativo do ditado atual (atualizado no início da gravação)
        self._active_translate = False
        self._active_auto_send = False
        self._active_quantum_brain = False

        # ---- Streaming mode -----------------------------------------------
        self._stream_session = None  # Instância ativa de StreamTranscriber
        self._stream_accumulated: list[str] = []  # Texto acumulado dos chunks
        self._stream_target_window = WindowTarget(0)  # Janela destino do streaming
        self._stream_auto_send = False

        # Registra atalhos de controle
        self.esc_hotkey = EscapeHotkey(self.cancel_from_thread)
        self.settings_window: SettingsWindow | None = None

        # Registra as 4 hotkeys globais editáveis
        self.hotkey_normal: GlobalHotkey | None = None
        self.hotkey_translate: GlobalHotkey | None = None
        self.hotkey_auto_send: GlobalHotkey | None = None
        self.hotkey_quantum_brain: GlobalHotkey | None = None
        self._register_all_hotkeys()

        # Ícone do sistema (systray)
        self.tray = TrayIcon(
            lambda: self.toggle_from_thread(translate=False, auto_send=False),
            self.open_config_from_thread,
            self.exit_from_thread,
        )

    def _register_all_hotkeys(self) -> None:
        """Desregistra atalhos antigos e registra as 4 hotkeys ativas de forma limpa."""
        self._unregister_all_hotkeys()

        # 1. Atalho Normal
        self.hotkey_normal = GlobalHotkey(
            getattr(self.config, "hotkey", "Ctrl+Space"),
            on_release=lambda: self.toggle_from_thread(translate=False, auto_send=False),
        )
        hk_trans = getattr(self.config, "hotkey_translate", "Ctrl+Alt+Space")
        self.hotkey_translate = GlobalHotkey(
            hk_trans,
            on_release=lambda: self.toggle_from_thread(translate=True, auto_send=False),
        ) if hk_trans else None
        hk_auto = getattr(self.config, "hotkey_auto_send", "Ctrl+Shift+Space")
        self.hotkey_auto_send = GlobalHotkey(
            hk_auto,
            on_release=lambda: self.toggle_from_thread(translate=False, auto_send=True),
        ) if hk_auto else None

        # 4. Atalho Quantum Brain
        hk_brain = getattr(self.config, "hotkey_quantum_brain", "Ctrl+Shift+D")
        self.hotkey_quantum_brain = GlobalHotkey(
            hk_brain,
            on_release=lambda: self.toggle_from_thread(translate=False, auto_send=False, quantum_brain=True),
        ) if hk_brain and getattr(self.config, "quantum_brain_enabled", True) else None

        # Inicializa as hotkeys no Windows
        for name, hk in [
            ("Normal", self.hotkey_normal),
            ("Tradução", self.hotkey_translate),
            ("Auto Enviar", self.hotkey_auto_send),
            ("Quantum Brain", self.hotkey_quantum_brain),
        ]:
            try:
                if hk:
                    hk.start()
            except RuntimeError as error:
                self.popup.show_message("Atalho indisponível", f"{name}: {error}", error=True)
                self.root.after(4000, self.popup.hide)

    def _unregister_all_hotkeys(self) -> None:
        """Encerra a escuta de todas as hotkeys registradas."""
        if getattr(self, "hotkey_normal", None):
            self.hotkey_normal.stop()
            self.hotkey_normal = None
        if getattr(self, "hotkey_translate", None):
            self.hotkey_translate.stop()
            self.hotkey_translate = None
        if getattr(self, "hotkey_auto_send", None):
            self.hotkey_auto_send.stop()
            self.hotkey_auto_send = None
        if getattr(self, "hotkey_quantum_brain", None):
            self.hotkey_quantum_brain.stop()
            self.hotkey_quantum_brain = None

    def run(self) -> None:
        """Inicia a aplicação executando os loops de escuta e o loop principal do Tkinter."""
        self.tray.start()
        # Primeira execução: instala o modelo padrão em segundo plano. A bandeja
        # permanece responsiva e o primeiro ditado aguarda o mesmo download, se preciso.
        if getattr(self.config, "auto_download_model", True):
            threading.Thread(target=self._prepare_model_download, daemon=True).start()
        # O CTranslate2 pode reservar vários GB e competir com o loop da bandeja
        # durante a carga. Por padrão o modelo é carregado somente após o primeiro
        # ditado; quem preferir aquecimento antecipado pode habilitar a opção no JSON.
        if getattr(self.config, "preload_model", False):
            threading.Thread(target=self._preload_model, daemon=True).start()
        self.root.mainloop()

    # ---- Callbacks disparados a partir de outras threads para execução segura na Main Thread ----

    def toggle_from_thread(self, translate: bool = False, auto_send: bool = False, quantum_brain: bool = False, *_args: object) -> None:
        """Função segura para thread chamar a UI."""
        self.root.after(0, lambda: self.toggle_recording(translate, auto_send, quantum_brain))

    def start_from_thread(self, translate: bool = False, auto_send: bool = False) -> None:
        self._last_press_time = threading.main_thread()  # apenas para inicializar se necessário, ou time.time()
        import time
        self._last_press_time = time.time()
        self.root.after(0, lambda: self._force_start_recording(translate, auto_send))

    def stop_from_thread(self) -> None:
        import time
        elapsed = time.time() - getattr(self, "_last_press_time", 0)
        delay = max(0, 0.45 - elapsed)
        if delay > 0:
            self.root.after(int(delay * 1000), self._force_stop_recording)
        else:
            self.root.after(0, self._force_stop_recording)

    def _force_start_recording(self, translate: bool, auto_send: bool) -> None:
        if not self.recorder.is_recording:
            self.toggle_recording(translate, auto_send)

    def _force_stop_recording(self) -> None:
        if self.recorder.is_recording:
            self.toggle_recording(self._active_translate, self._active_auto_send)

    def cancel_from_thread(self, *_args: object) -> None:
        """Cancela a gravação em andamento de forma segura na thread principal."""
        self.root.after(0, self.cancel_recording)

    def open_config_from_thread(self, *_args: object) -> None:
        """Abre o arquivo de configurações do usuário."""
        self.root.after(0, self.open_config)

    def exit_from_thread(self, *_args: object) -> None:
        """Encerra a aplicação de forma segura."""
        self.root.after(0, self.exit)

    def _on_hud_cancel(self) -> None:
        """Callback dinâmico do botão Cancelar do HUD.

        Roteia para o handler correto dependendo do estado atual:
        - Durante gravação → cancela a captura de áudio
        - Durante transcrição → cancela o processamento da IA
        """
        if self.processing:
            self.cancel_transcription()
        else:
            self.cancel_recording()

    # ---- Fluxos de Gravação ----

    def toggle_recording(self, translate: bool = False, auto_send: bool = False, quantum_brain: bool = False) -> None:
        """Inicia ou finaliza o processo de gravação baseado no estado atual."""
        if self.processing or self.starting:
            return

        # ---- Modo Streaming ------------------------------------------------
        if self.config.streaming_mode and not translate and not quantum_brain:
            if self._stream_session is not None:
                # Streaming em andamento → para e entrega
                self._stop_streaming(auto_send)
            else:
                # Inicia nova sessão de streaming
                self.target_window = capture_input_target()
                self._active_auto_send = auto_send
                self._start_streaming()
            return

        # ---- Modo Clássico (push-to-talk) ----------------------------------
        if self.recorder.is_recording:
            # Finaliza a gravação usando os parâmetros que foram definidos no início
            self.finish_recording(self._active_translate, self._active_auto_send)
        else:
            # Captura a janela ativa de destino ANTES do início físico
            self.target_window = capture_input_target()
            self._active_translate = translate
            self._active_auto_send = auto_send
            self._active_quantum_brain = quantum_brain
            self.start_recording()

    def start_recording(self) -> None:
        """Inicia a captação do microfone e exibe o popup de gravação."""
        if self.starting:
            return
        if self.config.play_sounds:
            self.starting = True
            play_start_sound(self.config.sound_volume)
            # Atraso de 180ms para garantir que o som do bipe não seja gravado pelo microfone
            self.root.after(180, self._do_start_recording)
        else:
            self._do_start_recording()

    def get_configured_device_index(self) -> int | None:
        """Retorna o índice do dispositivo de áudio configurado no arquivo config.json."""
        from .audio import get_device_index_by_name
        return get_device_index_by_name(self.config.audio_device)

    def _on_recording_limit_reached(self) -> None:
        """Callback acionado quando a gravação atinge o limite máximo de tempo."""
        if self.recorder.is_recording:
            max_min = int(getattr(self.config, "max_recording_seconds", 600)) // 60
            self.root.after(0, lambda: self._show_error(f"Limite de {max_min} minutos atingido — gravação finalizada automaticamente."))
            self.root.after(0, self.toggle_recording)

    def _do_start_recording(self) -> None:
        """Inicia fisicamente a gravação de áudio do microfone."""
        self.starting = False
        try:
            device_index = self.get_configured_device_index()
            max_sec = float(getattr(self.config, "max_recording_seconds", 600))
            self.recorder.start(
                device_index=device_index,
                max_seconds=max_sec,
                on_limit_reached=self._on_recording_limit_reached
            )
        except Exception as error:
            self.popup.show_message("Microfone indisponível", str(error), error=True)
            self.root.after(5000, self.popup.hide)
            return

        # Registra a tecla Esc para cancelamento rápido enquanto grava
        self.esc_hotkey.register()
        self.popup.show_recording(theme=self.config.hud_theme, color=self.config.atom_color)

        # Define o subtítulo com base no tom e modo ativos
        if getattr(self, "_active_quantum_brain", False):
            sub_text = "Ctrl+Shift+D para concluir • 🧠 Quantum Brain"
        elif self._active_translate:
            sub_text = "Ctrl+Alt+Space para concluir • Inglês"
        elif self._active_auto_send:
            sub_text = "Ctrl+Shift+Space para concluir • Envio"
        else:
            # Exibe o tom ativo no rodapé do HUD
            sub_text = f"Ctrl+Space para concluir • Tom: {self.config.tone_style}"
        self.popup.set_text("Ouvindo…", sub_text)

    def finish_recording(self, translate: bool = False, auto_send: bool = False) -> None:
        """Finaliza a captação de áudio e inicia o pipeline assíncrono de transcrição."""
        self.processing = True
        self.esc_hotkey.unregister()

        audio_path = Path(tempfile.gettempdir()) / "localwhisper-recording.wav"
        try:
            # stop_and_save desliga o stream e gera o wav completo
            duration = self.recorder.stop_and_save(audio_path)
        except Exception as error:
            self.processing = False
            self.popup.show_message("Falha na gravação", str(error), error=True)
            self.root.after(5000, self.popup.hide)
            return

        # Verifica se o tempo de áudio é suficiente
        if duration < 0.25:
            self.processing = False
            self.popup.show_message("Gravação muito curta", "Tente falar por mais tempo.")
            self.root.after(2200, self.popup.hide)
            return

        # Salva cópia de segurança do WAV para emergência em %LOCALAPPDATA%\LocalWhisper\emergency_audio.wav
        import shutil

        from .config import app_data_dir
        try:
            emergency_path = app_data_dir() / "emergency_audio.wav"
            shutil.copy2(str(audio_path), str(emergency_path))
        except Exception as copy_err:
            print(f"[Aviso] Falha ao criar arquivo de emergência: {copy_err}")

        # Executa a chamada do Whisper em segundo plano para não congelar o HUD flutuante
        self._transcription_thread = threading.Thread(
            target=self._transcribe_and_deliver,
            args=(audio_path, self.target_window, duration, translate, auto_send),
            daemon=True,
        )
        self._transcription_thread.start()

    def cancel_recording(self) -> None:
        """Interrompe a gravação e descarta qualquer som capturado."""
        # Cancela streaming se estiver ativo
        if self._stream_session is not None:
            self._stream_session.cancel()
            self._stream_session = None
            self._stream_accumulated = []

        self.esc_hotkey.unregister()
        if self.recorder.is_recording:
            self.recorder.cancel()
            if self.config.play_sounds:
                play_cancel_sound(self.config.sound_volume)
        self.processing = False
        self.starting = False
        self.popup.hide()

    def cancel_transcription(self) -> None:
        """Cancela transcrição em andamento e fecha o HUD imediatamente."""
        self.transcriber.cancel()
        if self.config.play_sounds:
            play_cancel_sound(self.config.sound_volume)
        self.processing = False
        self.starting = False
        self.root.after(0, self.popup.hide)

    # ---- Pipeline de Entrega ----

    def _transcribe_and_deliver(
        self,
        audio_path: Path,
        target_window: WindowTarget,
        duration: float,
        translate: bool = False,
        auto_send: bool = False,
    ) -> None:
        """Transcreve o arquivo gravado e entrega o texto nos locais devidos.

        Roda inteiramente em uma thread secundária.
        """
        try:
            title_hud = "Traduzindo…" if translate else "Transcrevendo…"
            if not self.transcriber.is_loaded():
                self.root.after(0, self.popup.show_loading_model)
                self.transcriber.load()
                self.root.after(0, lambda: self.popup.show_processing_with_progress(duration, title_override=title_hud))
            else:
                self.root.after(0, lambda: self.popup.show_processing_with_progress(duration, title_override=title_hud))

            # Transcreve o áudio completo de uma só vez (muito mais rápido e sem bugs de picotamento)
            text = self.transcriber.transcribe(audio_path, translate=translate, duration=duration)

            # Guarda a transcrição bruta do Whisper antes do pós-processamento
            raw_text = text or ""

            if text and text.strip():
                literal_mode = bool(getattr(self.config, "literal_mode", True)) and not translate
                # ---- Limpeza pós-transcrição (determinística, zero latência) ----
                # Remove gageiras, alucinações, erros gram. óbvios e fillers
                try:
                    from .speech_cleaner import clean_transcription, parse_custom_fillers
                    custom_fillers_set = None
                    if getattr(self.config, 'remove_fillers', False):
                        raw_fillers_str = getattr(self.config, 'custom_fillers', '')
                        if raw_fillers_str:
                            custom_fillers_set = parse_custom_fillers(raw_fillers_str)
                    cleaned = clean_transcription(
                        text,
                        remove_stutter=getattr(self.config, 'remove_stutters', False),
                        remove_filler_words=getattr(self.config, 'remove_fillers', False),
                        custom_fillers=custom_fillers_set,
                        literal_mode=literal_mode,
                    )
                    if cleaned is None:
                        # Texto descartado como alucinação do Whisper
                        raise RuntimeError("Nenhuma fala detectada ou transcrição cancelada.")
                    text = cleaned
                except RuntimeError:
                    raise
                except Exception as clean_err:
                    print(f"[Aviso] Falha na limpeza de texto (usando bruto): {clean_err}")

                # ---- Dicionário personalizado (substituições exatas) ----
                if not literal_mode:
                    try:
                        from .post_processor import apply_custom_dict
                        if self.config.custom_dict:
                            text = apply_custom_dict(text, self.config.custom_dict)
                    except Exception as dict_err:
                        print(f"[Aviso] Falha ao aplicar dicionário personalizado: {dict_err}")

                # ---- Vocabulário pessoal (aprendido dos diários/correções) ----
                if not literal_mode:
                    try:
                        from .vocab_cache import personal_vocab
                        text = personal_vocab.apply_corrections(text)
                    except Exception as vocab_err:
                        print(f"[Aviso] Falha ao aplicar vocabulário pessoal: {vocab_err}")

                # 1. Cache Semântico rápido (Opção 3)
                if not literal_mode:
                    from .cache import global_cache
                    cached = global_cache.get(text) if self.config.use_llm_rewriter else None
                    if cached:
                        text = cached
                    else:
                        # 2. Mini-LLM de reescrita se habilitado
                        if self.config.use_llm_rewriter:
                            from .rewriter import _should_skip_rewriter, rewrite_text
                            # Guard: não acionar o LLM para frases muito curtas
                            if _should_skip_rewriter(text):
                                pass  # Usa o texto original do Whisper
                            else:
                                try:
                                    # O HUD mostra "Reescrevendo..." durante o processamento do LLM
                                    self.root.after(0, lambda: self.popup.set_text("Reescrevendo...", "IA Ativada"))

                                    from .hardware import resolve_hardware
                                    hardware = resolve_hardware(self.config.device, self.config.compute_type)
                                    device = hardware.device
                                    compute_type = hardware.compute_type

                                    # Executa com watchdog de 15s para evitar congelamento
                                    import concurrent.futures
                                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as llm_executor:
                                        llm_future = llm_executor.submit(
                                            rewrite_text,
                                            text,
                                            self.config.tone_style,
                                            self.config.llm_model_repo,
                                            device=device,
                                            compute_type=compute_type,
                                            is_translation=translate
                                        )
                                        refined = llm_future.result(timeout=15.0)

                                    # Alimenta o cache com a correspondência
                                    global_cache.set(text, refined)
                                    text = refined
                                except Exception as e:
                                    print(f"[Aviso] Falha ao reescrever texto com Mini-LLM (usando original): {e}")

            if not text or not text.strip():
                raise RuntimeError("Nenhuma fala detectada ou transcrição cancelada.")

            self.root.after(0, self.popup.complete_progress)

            # 1. Copia e/ou injeta o texto de forma eficiente
            typed = False
            should_paste = self.config.auto_paste
            if getattr(self, "_active_quantum_brain", False) and not getattr(self.config, "quantum_brain_also_paste", True):
                should_paste = False

            if should_paste:
                # type_into_window já copia para o clipboard internamente
                typed = type_into_window(target_window, text)

                # Se atalho de auto-envio (auto_send) foi acionado e a colagem funcionou, dá Enter
                if auto_send and typed:
                    press_enter()
            else:
                # Se não vai colar automaticamente, apenas copia para a área de transferência
                set_clipboard_text(text)

            # --- Quantum Brain: salva nota se o modo estiver ativo ---
            if getattr(self, "_active_quantum_brain", False) and text and text.strip():
                try:
                    from .quantum_brain import QuantumBrainOrchestrator
                    orchestrator = QuantumBrainOrchestrator.get_instance(self.config)
                    orchestrator.add_entry(text)
                except Exception as qb_err:
                    print(f"[Quantum Brain] Erro ao salvar nota: {qb_err}")

            # 3. Adiciona entrada no diário pessoal do dia (.md)
            try:
                save_entry(text)
            except Exception:
                pass

            # 4. Salva o histórico comparativo das transcrições (Debug)
            try:
                from .diary import save_comparison_log
                save_comparison_log(
                    raw_text=raw_text,
                    processed_text=text,
                    tone=self.config.tone_style,
                    rewriter_active=self.config.use_llm_rewriter
                )
            except Exception as log_error:
                print(f"[Aviso] Falha ao salvar log comparativo: {log_error}")

            message = "Texto inserido e enviado" if (typed and auto_send) else ("Texto inserido" if typed else "Texto copiado")
            self.root.after(0, lambda m=message: self._show_success(m))

            # Transcrição concluída com sucesso: remove o arquivo de emergência
            from .config import app_data_dir
            try:
                (app_data_dir() / "emergency_audio.wav").unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as error:
            err_msg = str(error)
            self.root.after(0, lambda e=err_msg: self._show_error(e))
        finally:
            self.processing = False
            try:
                audio_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _show_success(self, message: str) -> None:
        """Mostra status de conclusão e agenda o fechamento automático do popup."""
        if self.config.play_sounds:
            play_end_sound(self.config.sound_volume)
        self.popup.show_message(message, "Disponível na área de transferência")
        self.root.after(1600, self.popup.hide)

    def _show_error(self, message: str) -> None:
        """Mostra mensagem de falha no popup e agenda o fechamento automático tardio."""
        self.popup.show_message("Não foi possível transcrever", message, error=True)
        self.root.after(6000, self.popup.hide)

    def _threadsafe_status(self, status: str) -> None:
        """Atualiza a mensagem de status no popup de forma assíncrona/thread-safe."""
        if self.processing:
            self.root.after(0, lambda s=status: self.popup.set_text(s, "Processamento local"))

    def _preload_model(self) -> None:
        """Instancia o modelo na inicialização para evitar gargalo de carregamento."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            self.transcriber.load()
        except Exception as e:
            logger.warning(f"[Preload] Falha ao pré-carregar modelo: {e}")
        try:
            if self.config.use_llm_rewriter:
                from .rewriter import _load_rewriter, is_rewriter_downloaded
                repo = self.config.llm_model_repo
                if is_rewriter_downloaded(repo):
                    # Resolve o hardware e precisão dinâmicos
                    from .hardware import resolve_hardware
                    hardware = resolve_hardware(self.config.device, self.config.compute_type)
                    device = hardware.device
                    compute_type = hardware.compute_type
                    _load_rewriter(repo, device=device, compute_type=compute_type)
        except Exception:
            pass
        # Pré-aquece o Silero VAD se o streaming estiver ativado
        if self.config.streaming_mode:
            try:
                from .stream_transcriber import _create_best_vad
                _create_best_vad()  # Carrega o modelo torch na memória
            except Exception:
                pass

    def _prepare_model_download(self) -> None:
        """Baixa o modelo escolhido sem ocupar CPU/GPU carregando-o na memória."""
        from .config import is_model_downloaded
        from .model_manager import ensure_model_downloaded

        model_name = getattr(self.config, "effective_model", "") or self.config.model
        if is_model_downloaded(model_name):
            return
        try:
            self.tray.icon.title = f"Quantum Scribe — Baixando modelo {model_name}..."
        except Exception:
            pass
        try:
            ensure_model_downloaded(model_name)
            try:
                self.tray.icon.title = "Quantum Scribe — Pronto para ditar"
            except Exception:
                pass
        except Exception as error:
            import logging

            logging.getLogger(__name__).warning("[Modelo] Download automático falhou: %s", error)
            try:
                self.tray.icon.title = "Quantum Scribe — Download pendente; clique para tentar novamente"
            except Exception:
                pass

    # ---- Métodos de Streaming -----------------------------------------------

    def _start_streaming(self) -> None:
        """Inicia uma sessão de streaming contínuo."""
        from .stream_transcriber import StreamTranscriber

        self.processing = True
        self._stream_accumulated = []
        self._stream_target_window = self.target_window
        self._stream_auto_send = self._active_auto_send

        self._stream_session = StreamTranscriber(
            config=self.config,
            on_chunk_text=self._on_stream_chunk,
            on_status=self._threadsafe_status,
            on_error=lambda e: print(f"[Stream] Erro: {e}"),
        )

        device_index = self.get_configured_device_index()

        if self.config.play_sounds:
            play_start_sound(self.config.sound_volume)

        # Registra ESC para cancelar
        self.esc_hotkey.register()

        # Inicia o streaming em thread separada para não bloquear o HUD
        def _do_start():
            try:
                self._stream_session.start(self.transcriber, device_index=device_index)
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._show_error(err))
                self.processing = False
                self._stream_session = None

        threading.Thread(target=_do_start, daemon=True).start()

        # Exibe o HUD de streaming
        self.popup.show_recording(theme=self.config.hud_theme, color=self.config.atom_color)
        self.popup.set_text("Streaming…", "Ctrl+Space para finalizar • Transcrição contínua")

    def _stop_streaming(self, auto_send: bool = False) -> None:
        """Para o streaming e entrega o texto acumulado."""
        if self._stream_session is None:
            return

        session = self._stream_session
        self._stream_session = None
        self.esc_hotkey.unregister()

        self.popup.set_text("Finalizando…", "Processando último chunk")

        target = self._stream_target_window
        do_auto_send = auto_send or self._stream_auto_send

        def _finalize():
            try:
                # Para o stream e aguarda últimos chunks
                full_text = session.stop()

                if not full_text or not full_text.strip():
                    self.root.after(0, lambda: self._show_error("Nenhuma fala detectada."))
                    return

                # Salva no diário
                try:
                    from .diary import save_entry
                    save_entry(full_text)
                except Exception:
                    pass

                # Entrega o texto
                typed = False
                if self.config.auto_paste:
                    # type_into_window já copia para o clipboard internamente
                    typed = type_into_window(target, full_text)
                    if do_auto_send and typed:
                        press_enter()
                else:
                    # Se não vai colar automaticamente, apenas copia para a área de transferência
                    set_clipboard_text(full_text)

                if self.config.play_sounds:
                    play_end_sound(self.config.sound_volume)

                message = "Texto inserido e enviado" if (typed and do_auto_send) else (
                    "Texto inserido" if typed else "Texto copiado"
                )
                self.root.after(0, lambda m=message: self._show_success(m))
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._show_error(err))
            finally:
                self.processing = False

        threading.Thread(target=_finalize, daemon=True).start()

    def _on_stream_chunk(self, chunk_text: str) -> None:
        """Callback chamado quando um chunk do streaming foi transcrito.

        Atualiza o HUD com preview do texto acumulado.
        """
        self._stream_accumulated.append(chunk_text)
        count = len(self._stream_accumulated)
        preview = chunk_text[:50] + ("…" if len(chunk_text) > 50 else "")
        self.root.after(
            0,
            lambda p=preview, n=count: self.popup.set_text(
                f"Chunk {n} pronto",
                f"\"{p}\"",
            ),
        )

    def open_config(self) -> None:
        """Abre a interface gráfica de configurações do aplicativo."""
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        self.settings_window = SettingsWindow(self.root, self.config, self.save_and_apply_config)

    def save_and_apply_config(self, new_config: AppConfig) -> None:
        """Salva a nova configuração em disco e aplica dinamicamente na execução."""
        new_config.effective_model = new_config.model
        save_config(new_config)

        # Verifica se as hotkeys mudaram
        hk_changed = (
            self.config.hotkey != new_config.hotkey or
            getattr(self.config, "hotkey_translate", "Ctrl+Alt+Space") != getattr(new_config, "hotkey_translate", "Ctrl+Alt+Space") or
            getattr(self.config, "hotkey_auto_send", "Ctrl+Shift+Space") != getattr(new_config, "hotkey_auto_send", "Ctrl+Shift+Space") or
            getattr(self.config, "hotkey_quantum_brain", "Ctrl+Shift+D") != getattr(new_config, "hotkey_quantum_brain", "Ctrl+Shift+D") or
            getattr(self.config, "quantum_brain_enabled", True) != getattr(new_config, "quantum_brain_enabled", True)
        )

        self.config = new_config
        self.popup.config = new_config

        if hk_changed:
            self._register_all_hotkeys()

        self.transcriber.reload_config(new_config)
        if getattr(new_config, "auto_download_model", True):
            threading.Thread(target=self._prepare_model_download, daemon=True).start()

    def exit(self) -> None:
        """Desregistra recursos do sistema e encerra o processo de forma limpa."""
        from .config import app_data_dir
        pid_file = app_data_dir() / "instance.pid"
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:
            pass
        self.esc_hotkey.unregister()
        self.recorder.cancel()
        self._unregister_all_hotkeys()
        self.tray.stop()
        self.root.quit()


def main() -> None:
    """Ponto de entrada do executável."""
    # Migração transparente de dados legados (executa apenas uma vez)
    from .config import app_data_dir, migrate_legacy_data
    migrate_legacy_data()

    if not acquire_single_instance():
        import os
        import subprocess
        import sys
        import time
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        # Pergunta de forma amigável se deseja reiniciar o app
        resposta = messagebox.askyesno(
            "Quantum Scribe já ativo",
            "O Quantum Scribe já está aberto em segundo plano na bandeja do sistema.\n\n"
            "Deseja fechar a instância anterior e iniciar uma nova?",
            parent=root
        )
        root.destroy()

        if resposta:
            current_pid = os.getpid()
            pid_file = app_data_dir() / "instance.pid"

            other_pid = None
            if pid_file.exists():
                try:
                    other_pid = int(pid_file.read_text().strip())
                except (ValueError, OSError):
                    other_pid = None

            if other_pid and other_pid != current_pid:
                # Encerra APENAS a instância anterior do Quantum Scribe pelo PID exato
                cmd = (
                    f'powershell -WindowStyle Hidden -Command '
                    f'"Stop-Process -Id {other_pid} -ErrorAction SilentlyContinue"'
                )
                try:
                    subprocess.run(
                        cmd, shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                except Exception:
                    pass

            # Aguarda um pequeno instante para liberação do Mutex
            time.sleep(0.5)

            # Tenta adquirir o Mutex novamente
            if acquire_single_instance():
                pid_file.write_text(str(current_pid))
                app = QuantumScribeApp()
                app.run()
                return
        return

    # Salva o PID atual na inicialização bem-sucedida
    import os
    pid_file = app_data_dir() / "instance.pid"
    pid_file.write_text(str(os.getpid()))

    app = QuantumScribeApp()
    app.run()

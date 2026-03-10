from core.bootstrap import setup_environment
from core.logger import log_error, log_info, log_warning
from utils.cleaner import limpiar_output_ejecucion


def main():
    setup_context = setup_environment()

    from core.runner import new_qa_state, print_final_summary, run_full_process, validate_cleanup_integrity

    qa_state = new_qa_state()
    try:
        limpiar_output_ejecucion()
        validate_cleanup_integrity(qa_state, setup_context)
        log_info("\U0001F9F9 Limpieza previa completada")
        qa_state = run_full_process(qa_state=qa_state)
    except KeyboardInterrupt:
        qa_state["fatal_error"] = "Proceso interrumpido por el usuario"
        qa_state["exportacion_correcta"] = False
        log_warning("\u26A0\uFE0F Proceso interrumpido por el usuario")
    except Exception as exc:
        qa_state["fatal_error"] = str(exc)
        qa_state["exportacion_correcta"] = False
        log_error(f"\u274C Error global \u2192 {exc}")
    finally:
        print_final_summary(qa_state)


if __name__ == "__main__":
    main()

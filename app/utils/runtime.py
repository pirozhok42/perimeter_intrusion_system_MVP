import os


def configure_runtime(cpu_threads: int = 2):
    """
    Keeps GUI responsive during heavy CV inference.

    This does not disable any feature.
    It only prevents OpenCV / Torch / MKL / OpenMP from taking all CPU threads.
    """

    cpu_threads = max(1, int(cpu_threads))

    os.environ.setdefault("OMP_NUM_THREADS", str(cpu_threads))
    os.environ.setdefault("MKL_NUM_THREADS", str(cpu_threads))
    os.environ.setdefault("NUMEXPR_NUM_THREADS", str(cpu_threads))
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

    try:
        import cv2
        cv2.setNumThreads(0)
    except Exception:
        pass

    try:
        import torch
        torch.set_num_threads(cpu_threads)
        torch.set_num_interop_threads(1)
    except Exception:
        pass

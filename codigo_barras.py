"""Leitura de códigos de barras usando a webcam e OpenCV contrib."""

from typing import Optional


def ler_codigo_webcam(camera: int = 0) -> Optional[str]:
    """Abre a webcam; pressione Q ou Esc para cancelar a leitura."""
    try:
        import cv2
    except ImportError as erro:
        raise RuntimeError(
            "A leitura por webcam requer opencv-contrib-python. "
            "Instale as dependências do projeto."
        ) from erro

    if not hasattr(cv2, "barcode"):
        raise RuntimeError(
            "O detector de código de barras não está disponível. "
            "Reinstale opencv-contrib-python."
        )

    captura = cv2.VideoCapture(camera)
    nome_janela = "Leitor de código de barras"
    janela_aberta = False
    try:
        if not captura.isOpened():
            raise RuntimeError(
                "Não foi possível acessar a webcam. Verifique a câmera e as permissões."
            )
        detector = cv2.barcode.BarcodeDetector()
        while True:
            sucesso, quadro = captura.read()
            if not sucesso:
                raise RuntimeError("Não foi possível obter imagem da webcam.")

            detectado, codigos, _, cantos = detector.detectAndDecodeWithType(quadro)
            if detectado and codigos:
                for codigo in codigos:
                    if codigo:
                        return codigo.strip()
            if cantos is not None:
                cv2.polylines(
                    quadro,
                    [pontos.astype("int32") for pontos in cantos],
                    True,
                    (0, 200, 0),
                    2,
                )
            cv2.putText(
                quadro,
                "Aponte para o codigo de barras | Q/Esc para cancelar",
                (12, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
            cv2.imshow(nome_janela, quadro)
            janela_aberta = True
            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):
                return None
    finally:
        captura.release()
        if janela_aberta:
            cv2.destroyWindow(nome_janela)

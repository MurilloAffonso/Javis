import sys
import cv2
import os
import yt_dlp

# Windows: console em cp1252 quebra ao imprimir emojis. Força UTF-8 na saída.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- CONFIGURAÇÕES ---
# O link do vídeo do Rafael que você enviou
URL_VIDEO = "https://www.youtube.com/watch?v=tAcKxn1crOc"

# Nome da pasta onde as fotos vão ser salvas
PASTA_DESTINO = "telas_extraidas_video"

# A cada quantos segundos o script deve tirar um print?
# Coloque 2 ou 3 para pegar muitos detalhes, ou 5 para um resumo geral
INTERVALO_SEGUNDOS = 5


def baixar_video(url):
    print("📥 Baixando o vídeo com a melhor qualidade...")
    opcoes = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': 'video_temp.mp4',
        'quiet': False,
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        ydl.download([url])
    return "video_temp.mp4"


def extrair_frames(caminho_video, pasta_saida, intervalo):
    print(f"📸 Extraindo um print a cada {intervalo} segundos...")
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    video = cv2.VideoCapture(caminho_video)
    fps = video.get(cv2.CAP_PROP_FPS)
    frames_pular = int(fps * intervalo)

    sucesso, frame = video.read()
    contador_frames = 0
    contador_imagens = 0

    while sucesso:
        if contador_frames % frames_pular == 0:
            # Salva o frame como imagem JPG
            nome_arquivo = os.path.join(pasta_saida, f"tela_{contador_imagens:04d}.jpg")
            cv2.imwrite(nome_arquivo, frame)
            contador_imagens += 1

        sucesso, frame = video.read()
        contador_frames += 1

    video.release()
    print(f"✅ Pronto! {contador_imagens} imagens foram salvas na pasta '{pasta_saida}'.")


if __name__ == "__main__":
    try:
        video_baixado = baixar_video(URL_VIDEO)
        extrair_frames(video_baixado, PASTA_DESTINO, INTERVALO_SEGUNDOS)

        # Limpeza: apaga o arquivo de vídeo pesado após extrair as fotos
        if os.path.exists(video_baixado):
            os.remove(video_baixado)
            print("🗑️ Arquivo de vídeo temporário apagado.")

    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import yt_dlp
import os
import subprocess
import re

def escolher_pasta():
    pasta = filedialog.askdirectory()
    if pasta:
        pasta_saida.set(pasta)

def baixar_playlist():
    url = entrada_url.get()
    pasta = pasta_saida.get()

    if not url.strip():
        messagebox.showwarning("Aviso", "Cole o link da playlist primeiro!")
        return
    if not pasta.strip():
        messagebox.showwarning("Aviso", "Escolha uma pasta de destino!")
        return

    texto_status.set("Baixando... Aguarde.")

    def processo():
        try:
            if not os.path.exists(pasta):
                os.makedirs(pasta)

            # Baixar os vídeos da playlist
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(pasta, "%(playlist_index)02d.%(ext)s"),  # 01,02...
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            texto_status.set("Preparando lista de arquivos...")

            # Lista todos os MP3 na pasta
            mp3_files = [f for f in os.listdir(pasta) if f.lower().endswith(".mp3")]
            if not mp3_files:
                raise Exception("Nenhum arquivo MP3 encontrado!")

            # Renomeia 01.mp3, 02.mp3… para 1.mp3, 2.mp3…
            safe_files = []
            for f in sorted(mp3_files):
                old_path = os.path.join(pasta, f)
                match = re.match(r"0*(\d+)", f)  # captura o número ignorando zeros à esquerda
                if not match:
                    continue
                index = int(match.group(1))
                new_name = f"{index}.mp3"
                new_path = os.path.join(pasta, new_name)
                os.rename(old_path, new_path)
                safe_files.append(new_path)

            # Cria lista.txt para concatenação (UTF-8 sem BOM)
            list_file = os.path.join(pasta, "lista.txt")
            with open(list_file, "w", encoding="utf-8") as f:
                for mp3 in safe_files:
                    caminho = os.path.abspath(mp3).replace("\\", "/")
                    f.write(f"file '{caminho}'\n")

            texto_status.set("Unindo todos os MP3...")

            # Define arquivo final sem sobrescrever
            final_mp3 = os.path.join(pasta, "playlist_final.mp3")
            contador = 1
            while os.path.exists(final_mp3):
                final_mp3 = os.path.join(pasta, f"playlist_final_{contador}.mp3")
                contador += 1

            # Roda FFmpeg e captura saída de erro completa
            result = subprocess.run(
                ["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file,
                 "-c:a", "libmp3lame", "-b:a", "192k", final_mp3],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"FFmpeg retornou erro:\n{result.stderr}")

            # Remove arquivos individuais e lista.txt
            for mp3 in safe_files:
                os.remove(mp3)
            os.remove(list_file)

            texto_status.set("Tudo pronto!")
            messagebox.showinfo("Sucesso", f"Playlist compilada em:\n{final_mp3}")

        except Exception as e:
            texto_status.set("Erro ao baixar!")
            messagebox.showerror("Erro", str(e))

    threading.Thread(target=processo).start()

# ---------------- INTERFACE ----------------
janela = tk.Tk()
janela.title("Downloader de Playlist YouTube → MP3 Único")
janela.geometry("500x250")

tk.Label(janela, text="Link da Playlist:").pack(pady=5)
entrada_url = tk.Entry(janela, width=60)
entrada_url.pack(pady=5)

tk.Label(janela, text="Pasta de destino:").pack(pady=5)
pasta_saida = tk.StringVar()
entrada_pasta = tk.Entry(janela, textvariable=pasta_saida, width=45)
entrada_pasta.pack(side=tk.LEFT, padx=5, pady=5)
btn_pasta = tk.Button(janela, text="Procurar", command=escolher_pasta)
btn_pasta.pack(side=tk.LEFT, padx=5, pady=5)

tk.Button(janela, text="Baixar e Compilar", command=baixar_playlist).pack(pady=15)

texto_status = tk.StringVar()
texto_status.set("Aguardando link...")
tk.Label(janela, textvariable=texto_status, fg="blue").pack(pady=10)

janela.mainloop()

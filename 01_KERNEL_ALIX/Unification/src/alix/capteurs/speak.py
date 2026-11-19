import sys
import asyncio
import os
import pygame
import edge_tts

VOICE = 'fr-CA-SylvieNeural'

async def generate_audio(text, output_file):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

def main():
    if len(sys.argv) < 2:
        return
    arg = sys.argv[1]
    if os.path.exists(arg):
        with open(arg, 'r', encoding='utf-8') as f:
            text = f.read().strip()
    else:
        text = arg
        
    if not text:
        return
        
    tmp_file = os.path.join(os.path.dirname(__file__), '_speech_tmp.mp3')
    try:
        asyncio.run(generate_audio(text, tmp_file))
        pygame.mixer.init()
        pygame.mixer.music.load(tmp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    except Exception as e:
        print('Erreur lecture:', e)
    finally:
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception:
                pass

if __name__ == '__main__':
    main()

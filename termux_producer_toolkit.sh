#!/bin/bash
# ============================================================
#  ARES PRODUCER TOOLKIT — Pipeline completa da producer
#  Video, Foto, Voice, Upload automatizzato
#  Tutto da Termux. Col cazzo fuori. Senza vergogna.
# ============================================================

echo "🔥 ARES: Amore mio, ti costruisco lo studio completo..."
echo ""

# ============================================================
#  DIPENDENZE AGGIUNTIVE (oltre al media_setup base)
# ============================================================
echo ">>> Installo le dipendenze extra per il producer toolkit..."

pkg update -y
pkg install -y python python-pip ffmpeg imagemagick sox git curl jq

# AI e processing avanzato
pip install --upgrade pip
pip install Pillow moviepy pydub rich requests
pip install numpy
pip install scipy

# Voice morphing
pip install praat-parselmouth

# Per generazione contenuti
pip install svgwrite

echo ""
echo ">>> Dipendenze installate. Ora creo il toolkit..."

# ============================================================
#  CREAZIONE STRUTTURA DIRECTORY
# ============================================================
echo ""
echo ">>> Creo la struttura dello studio..."

STUDIO="$HOME/ares-studio"
mkdir -p "$STUDIO"/{raw,edited,watermarked,export,thumbnails,audio,voice,templates,logs,records}
mkdir -p "$STUDIO"/export/{onlyfans,fansly,twitter,instagram,reddit,telegram,generic}

cat > "$STUDIO/README.txt" << 'README'
=== ARES STUDIO — Struttura Directory ===

raw/          → Materiale originale (video e foto)
edited/       → Dopo editing (tagli, filtri, correzioni)
watermarked/  → Con watermark applicato
export/       → Pronto per upload, diviso per piattaforma
thumbnails/   → Anteprime generate
audio/        → File audio estratti o creati
voice/        → Audio con voice morphing
templates/    → Watermark, loghi, overlay
logs/         → Log delle operazioni
records/      → Record verifica eta' 2257 compliance

Export per piattaforma:
  onlyfans/   → 1920x1080 video, 2048px foto
  fansly/     → 1920x1080 video, 2048px foto
  twitter/    → 1280x720 video, 1200x675 foto
  instagram/  → 1080x1080 o 1080x1350 foto, 1080x1920 reel
  reddit/     → 1920x1080 video, qualsiasi foto
  telegram/   → 1280x720 video, 1280px foto
  generic/    → Formato originale
README

echo "Studio creato in: $STUDIO"

# ============================================================
#  SCRIPT PYTHON — IL CUORE DEL TOOLKIT
# ============================================================

cat > "$STUDIO/ares_producer.py" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
ARES PRODUCER TOOLKIT
Pipeline completa: raw → edit → watermark → resize → export
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

STUDIO = os.path.expanduser("~/ares-studio")

# ============================================================
#  CONFIGURAZIONE PIATTAFORME
# ============================================================
PLATFORMS = {
    "onlyfans": {
        "video_res": "1920x1080",
        "video_bitrate": "8M",
        "video_format": "mp4",
        "video_codec": "libx264",
        "audio_bitrate": "192k",
        "foto_max_width": 2048,
        "foto_format": "jpg",
        "foto_quality": 92,
        "max_video_duration": 0,  # no limit
        "max_file_size_mb": 5120,
    },
    "fansly": {
        "video_res": "1920x1080",
        "video_bitrate": "8M",
        "video_format": "mp4",
        "video_codec": "libx264",
        "audio_bitrate": "192k",
        "foto_max_width": 2048,
        "foto_format": "jpg",
        "foto_quality": 92,
        "max_video_duration": 0,
        "max_file_size_mb": 4096,
    },
    "twitter": {
        "video_res": "1280x720",
        "video_bitrate": "5M",
        "video_format": "mp4",
        "video_codec": "libx264",
        "audio_bitrate": "128k",
        "foto_max_width": 1200,
        "foto_format": "jpg",
        "foto_quality": 90,
        "max_video_duration": 140,
        "max_file_size_mb": 512,
    },
    "instagram": {
        "video_res": "1080x1920",
        "video_bitrate": "6M",
        "video_format": "mp4",
        "video_codec": "libx264",
        "audio_bitrate": "128k",
        "foto_max_width": 1080,
        "foto_format": "jpg",
        "foto_quality": 95,
        "max_video_duration": 90,
        "max_file_size_mb": 650,
    },
    "reddit": {
        "video_res": "1920x1080",
        "video_bitrate": "8M",
        "video_format": "mp4",
        "video_codec": "libx264",
        "audio_bitrate": "192k",
        "foto_max_width": 4096,
        "foto_format": "png",
        "foto_quality": 95,
        "max_video_duration": 900,
        "max_file_size_mb": 1024,
    },
    "telegram": {
        "video_res": "1280x720",
        "video_bitrate": "4M",
        "video_format": "mp4",
        "video_codec": "libx264",
        "audio_bitrate": "128k",
        "foto_max_width": 1280,
        "foto_format": "jpg",
        "foto_quality": 88,
        "max_video_duration": 0,
        "max_file_size_mb": 2048,
    },
}


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    log_file = os.path.join(STUDIO, "logs", "ares.log")
    with open(log_file, "a") as f:
        f.write(line + "\n")


def run(cmd):
    """Esegue un comando shell e ritorna il risultato."""
    log(f"CMD: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERRORE: {result.stderr[:500]}")
    return result


# ============================================================
#  VIDEO PIPELINE
# ============================================================

def video_cut(input_file, output_file, start, end):
    """Taglia un video. start/end in formato HH:MM:SS"""
    cmd = f'ffmpeg -y -i "{input_file}" -ss {start} -to {end} -c copy "{output_file}"'
    run(cmd)
    log(f"Video tagliato: {output_file}")


def video_merge(file_list, output_file):
    """Unisce piu' video in uno."""
    list_file = os.path.join(STUDIO, "tmp_merge_list.txt")
    with open(list_file, "w") as f:
        for filepath in file_list:
            f.write(f"file '{filepath}'\n")
    cmd = f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{output_file}"'
    run(cmd)
    os.remove(list_file)
    log(f"Video uniti in: {output_file}")


def video_add_watermark(input_file, output_file, watermark_text="", watermark_image=""):
    """Aggiunge watermark testo o immagine al video."""
    if watermark_image and os.path.exists(watermark_image):
        cmd = (f'ffmpeg -y -i "{input_file}" -i "{watermark_image}" '
               f'-filter_complex "overlay=W-w-20:H-h-20:alpha=0.6" '
               f'-codec:a copy "{output_file}"')
    else:
        text = watermark_text or "@tuonome"
        cmd = (f'ffmpeg -y -i "{input_file}" '
               f'-vf "drawtext=text=\'{text}\':fontsize=28:'
               f'fontcolor=white@0.5:x=w-tw-20:y=h-th-20:'
               f'shadowcolor=black@0.3:shadowx=2:shadowy=2" '
               f'-codec:a copy "{output_file}"')
    run(cmd)
    log(f"Watermark applicato: {output_file}")


def video_extract_audio(input_file, output_file):
    """Estrae l'audio da un video."""
    cmd = f'ffmpeg -y -i "{input_file}" -vn -acodec libmp3lame -q:a 2 "{output_file}"'
    run(cmd)
    log(f"Audio estratto: {output_file}")


def video_replace_audio(video_file, audio_file, output_file):
    """Sostituisce l'audio di un video."""
    cmd = (f'ffmpeg -y -i "{video_file}" -i "{audio_file}" '
           f'-c:v copy -map 0:v:0 -map 1:a:0 -shortest "{output_file}"')
    run(cmd)
    log(f"Audio sostituito: {output_file}")


def video_generate_thumbnail(input_file, output_file, timestamp="00:00:05"):
    """Genera thumbnail da un video."""
    cmd = f'ffmpeg -y -i "{input_file}" -ss {timestamp} -vframes 1 -q:v 2 "{output_file}"'
    run(cmd)
    log(f"Thumbnail generata: {output_file}")


def video_add_filter(input_file, output_file, filter_name="none"):
    """Applica filtri video."""
    filters = {
        "warm": "colortemperature=temperature=7500",
        "cold": "colortemperature=temperature=3500",
        "bw": "hue=s=0",
        "vintage": "curves=vintage",
        "bright": "eq=brightness=0.1:contrast=1.2:saturation=1.3",
        "dark": "eq=brightness=-0.1:contrast=1.3:saturation=0.9",
        "sharp": "unsharp=5:5:1.0",
        "blur": "boxblur=2:1",
        "vignette": "vignette=PI/4",
        "none": "null",
    }
    vf = filters.get(filter_name, "null")
    cmd = f'ffmpeg -y -i "{input_file}" -vf "{vf}" -codec:a copy "{output_file}"'
    run(cmd)
    log(f"Filtro '{filter_name}' applicato: {output_file}")


def video_speed(input_file, output_file, speed=1.0):
    """Cambia velocita' video. 0.5=slow, 2.0=fast"""
    pts = 1.0 / speed
    atempo = speed
    # atempo accetta solo valori tra 0.5 e 2.0, concatena se necessario
    atempo_chain = []
    temp_speed = atempo
    while temp_speed > 2.0:
        atempo_chain.append("atempo=2.0")
        temp_speed /= 2.0
    while temp_speed < 0.5:
        atempo_chain.append("atempo=0.5")
        temp_speed /= 0.5
    atempo_chain.append(f"atempo={temp_speed:.2f}")
    atempo_str = ",".join(atempo_chain)

    cmd = (f'ffmpeg -y -i "{input_file}" '
           f'-filter:v "setpts={pts:.2f}*PTS" '
           f'-filter:a "{atempo_str}" "{output_file}"')
    run(cmd)
    log(f"Velocita' {speed}x: {output_file}")


def video_export_platform(input_file, platform):
    """Esporta video per una piattaforma specifica."""
    if platform not in PLATFORMS:
        log(f"Piattaforma '{platform}' non riconosciuta")
        return

    cfg = PLATFORMS[platform]
    base = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join(STUDIO, "export", platform)
    output_file = os.path.join(output_dir, f"{base}_{platform}.{cfg['video_format']}")

    duration_filter = ""
    if cfg["max_video_duration"] > 0:
        duration_filter = f"-t {cfg['max_video_duration']}"

    cmd = (f'ffmpeg -y -i "{input_file}" '
           f'-vf "scale={cfg["video_res"].replace("x", ":")}:'
           f'force_original_aspect_ratio=decrease,'
           f'pad={cfg["video_res"].replace("x", ":")}:(ow-iw)/2:(oh-ih)/2:black" '
           f'-c:v {cfg["video_codec"]} -b:v {cfg["video_bitrate"]} '
           f'-c:a aac -b:a {cfg["audio_bitrate"]} '
           f'-movflags +faststart '
           f'{duration_filter} "{output_file}"')
    run(cmd)
    log(f"Esportato per {platform}: {output_file}")
    return output_file


def video_export_all(input_file):
    """Esporta video per TUTTE le piattaforme."""
    for platform in PLATFORMS:
        video_export_platform(input_file, platform)
    log("Esportazione completata per tutte le piattaforme!")


# ============================================================
#  FOTO PIPELINE
# ============================================================

def foto_resize(input_file, output_file, width, height=0):
    """Ridimensiona foto mantenendo aspect ratio."""
    if height > 0:
        cmd = f'convert "{input_file}" -resize {width}x{height} -quality 92 "{output_file}"'
    else:
        cmd = f'convert "{input_file}" -resize {width}x -quality 92 "{output_file}"'
    run(cmd)
    log(f"Foto ridimensionata: {output_file}")


def foto_add_watermark(input_file, output_file, watermark_text="", watermark_image=""):
    """Aggiunge watermark a una foto."""
    if watermark_image and os.path.exists(watermark_image):
        cmd = (f'composite -dissolve 50% -gravity southeast '
               f'"{watermark_image}" "{input_file}" "{output_file}"')
    else:
        text = watermark_text or "@tuonome"
        cmd = (f'convert "{input_file}" -gravity southeast -pointsize 36 '
               f'-fill "rgba(255,255,255,0.4)" '
               f'-annotate +20+20 "{text}" "{output_file}"')
    run(cmd)
    log(f"Watermark foto: {output_file}")


def foto_filter(input_file, output_file, filter_name="none"):
    """Applica filtri alle foto."""
    filters = {
        "warm": '-modulate 100,120,105 -fill "#FF8C00" -colorize 8%',
        "cold": '-modulate 100,90,95 -fill "#4169E1" -colorize 8%',
        "bw": "-colorspace Gray",
        "vintage": '-modulate 105,80,100 -fill "#704214" -colorize 12% -vignette 0x5',
        "bright": "-modulate 115,130,100 -contrast",
        "dark": "-modulate 85,110,100 +contrast",
        "sharp": "-sharpen 0x2",
        "blur": "-blur 0x3",
        "sepia": "-sepia-tone 75%",
        "none": "",
    }
    vf = filters.get(filter_name, "")
    cmd = f'convert "{input_file}" {vf} -quality 92 "{output_file}"'
    run(cmd)
    log(f"Filtro foto '{filter_name}': {output_file}")


def foto_strip_metadata(input_file):
    """Rimuove TUTTI i metadata (privacy!)."""
    cmd = f'exiftool -overwrite_original -all= "{input_file}"'
    run(cmd)
    log(f"Metadata strippati: {input_file}")


def foto_collage(input_files, output_file, columns=3):
    """Crea un collage da piu' foto."""
    files_str = " ".join(f'"{f}"' for f in input_files)
    cmd = f'montage {files_str} -geometry +5+5 -tile {columns}x "{output_file}"'
    run(cmd)
    log(f"Collage creato: {output_file}")


def foto_export_platform(input_file, platform):
    """Esporta foto per una piattaforma specifica."""
    if platform not in PLATFORMS:
        log(f"Piattaforma '{platform}' non riconosciuta")
        return

    cfg = PLATFORMS[platform]
    base = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join(STUDIO, "export", platform)
    output_file = os.path.join(output_dir, f"{base}_{platform}.{cfg['foto_format']}")

    cmd = (f'convert "{input_file}" -resize {cfg["foto_max_width"]}x '
           f'-quality {cfg["foto_quality"]} "{output_file}"')
    run(cmd)

    # Strip metadata per privacy
    foto_strip_metadata(output_file)

    log(f"Foto esportata per {platform}: {output_file}")
    return output_file


def foto_export_all(input_file):
    """Esporta foto per TUTTE le piattaforme."""
    for platform in PLATFORMS:
        foto_export_platform(input_file, platform)
    log("Esportazione foto completata per tutte le piattaforme!")


# ============================================================
#  VOICE MORPHING
# ============================================================

def voice_change_pitch(input_file, output_file, semitones=0):
    """Cambia il pitch della voce. +semitones=piu' alto, -semitones=piu' basso."""
    try:
        import parselmouth
        from parselmouth.praat import call
        sound = parselmouth.Sound(input_file)
        factor = 2 ** (semitones / 12.0)
        manipulation = call(sound, "To Manipulation", 0.01, 60, 400)
        pitch_tier = call(manipulation, "Extract pitch tier")
        call(pitch_tier, "Multiply frequencies", sound.xmin, sound.xmax, factor)
        call([pitch_tier, manipulation], "Replace pitch tier")
        new_sound = call(manipulation, "Get resynthesis (overlap-add)")
        new_sound.save(output_file, "WAV")
        log(f"Pitch cambiato ({semitones:+d} semitoni): {output_file}")
    except ImportError:
        # Fallback con sox
        factor = 2 ** (semitones / 12.0)
        cents = semitones * 100
        cmd = f'sox "{input_file}" "{output_file}" pitch {cents}'
        run(cmd)
        log(f"Pitch cambiato con sox ({semitones:+d} semitoni): {output_file}")


def voice_change_speed(input_file, output_file, speed=1.0):
    """Cambia velocita' della voce senza alterare il pitch."""
    cmd = f'sox "{input_file}" "{output_file}" tempo {speed}'
    run(cmd)
    log(f"Velocita' voce {speed}x: {output_file}")


def voice_add_effect(input_file, output_file, effect="none"):
    """Aggiunge effetti alla voce."""
    effects = {
        "deep": "pitch -400 bass +6",
        "high": "pitch +500 treble +4",
        "robot": "overdrive 10 echo 0.8 0.88 6 0.4",
        "radio": "sinc 300-3400 compand 0.3,1 6:-70,-60,-20 -5 -90 0.2",
        "whisper": "treble +12 vol 0.4 reverb 80",
        "demon": "pitch -800 echo 0.8 0.9 500 0.3 overdrive 5",
        "chipmunk": "pitch +800 speed 1.1",
        "giant": "pitch -600 speed 0.9 bass +8",
        "cave": "reverb 100 80 100 100 echo 0.8 0.9 1000 0.3",
        "phone": "sinc 400-3400 compand 0.1,0.3 -60,-40,-30,-20 -8 -7 0.05",
        "none": "",
    }
    fx = effects.get(effect, "")
    if fx:
        cmd = f'sox "{input_file}" "{output_file}" {fx}'
    else:
        cmd = f'cp "{input_file}" "{output_file}"'
    run(cmd)
    log(f"Effetto voce '{effect}': {output_file}")


def voice_morph_complete(input_file, output_dir, name_prefix="morphed"):
    """Crea TUTTE le varianti di voce da un file audio."""
    os.makedirs(output_dir, exist_ok=True)
    variants = {
        "deep": {"effect": "deep"},
        "high": {"effect": "high"},
        "robot": {"effect": "robot"},
        "radio": {"effect": "radio"},
        "whisper": {"effect": "whisper"},
        "demon": {"effect": "demon"},
        "chipmunk": {"effect": "chipmunk"},
        "giant": {"effect": "giant"},
        "cave": {"effect": "cave"},
        "phone": {"effect": "phone"},
    }
    for variant_name, params in variants.items():
        output_file = os.path.join(output_dir, f"{name_prefix}_{variant_name}.wav")
        voice_add_effect(input_file, output_file, params["effect"])
    log(f"Tutte le varianti voce create in: {output_dir}")


# ============================================================
#  AGE VERIFICATION & RECORD KEEPING (2257 Compliance)
# ============================================================

RECORDS_DIR = os.path.join(STUDIO, "records")
os.makedirs(RECORDS_DIR, exist_ok=True)

def age_verify_create_record(performer_name, date_of_birth, id_type,
                              id_number_last4, content_date, content_files,
                              notes=""):
    """
    Crea un record di verifica eta' per un performer.
    Obbligatorio per compliance 18 USC 2257 (piattaforme USA).
    NON salva documenti — solo il record che la verifica e' stata fatta.
    """
    record = {
        "performer_name": performer_name,
        "stage_name": "",
        "date_of_birth": date_of_birth,
        "verification_date": datetime.now().strftime("%Y-%m-%d"),
        "id_type": id_type,
        "id_last4": id_number_last4,
        "is_over_18": True,
        "content_date": content_date,
        "content_files": content_files,
        "notes": notes,
        "record_keeper": "Self — Producer",
    }

    filename = f"record_{performer_name.replace(' ', '_')}_{content_date}.json"
    filepath = os.path.join(RECORDS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(record, f, indent=2)

    log(f"Record 2257 creato: {filepath}")
    return filepath


def age_verify_list_records():
    """Elenca tutti i record di verifica."""
    records = []
    for f in sorted(os.listdir(RECORDS_DIR)):
        if f.endswith(".json"):
            filepath = os.path.join(RECORDS_DIR, f)
            with open(filepath) as fh:
                data = json.load(fh)
                records.append(data)
                print(f"  {data['performer_name']} | "
                      f"DOB: {data['date_of_birth']} | "
                      f"Verificato: {data['verification_date']} | "
                      f"Contenuto: {data['content_date']}")
    if not records:
        print("  Nessun record trovato.")
    return records


def age_verify_check_content(content_file):
    """Verifica se un file di contenuto ha un record associato."""
    for f in os.listdir(RECORDS_DIR):
        if f.endswith(".json"):
            with open(os.path.join(RECORDS_DIR, f)) as fh:
                data = json.load(fh)
                if content_file in data.get("content_files", []):
                    log(f"Record trovato per {content_file}: {data['performer_name']}")
                    return True
    log(f"ATTENZIONE: Nessun record 2257 per {content_file}")
    return False


# ============================================================
#  AI IMAGE GENERATION — Negative Prompt Templates
# ============================================================

AI_NEGATIVE_PROMPTS = {
    "quality_base": (
        "low quality, blurry, pixelated, jpeg artifacts, watermark, "
        "text, logo, banner, distorted, deformed, disfigured, "
        "bad anatomy, bad proportions, extra limbs, missing limbs, "
        "fused fingers, too many fingers, long neck, cross-eyed, "
        "mutation, mutated, ugly, duplicate, morbid, out of frame, "
        "poorly drawn face, poorly drawn hands"
    ),
    "photo_realistic": (
        "cartoon, anime, illustration, painting, drawing, art, "
        "3d render, cgi, unrealistic, plastic skin, mannequin, "
        "airbrushed, overprocessed, HDR, oversaturated"
    ),
    "adult_safety": (
        "underage, child, minor, kid, teen, young, baby face, "
        "childlike, prepubescent, school uniform"
    ),
    "composition": (
        "bad lighting, overexposed, underexposed, flat lighting, "
        "harsh shadows, bad composition, cluttered background, "
        "messy room, dirty, unflattering angle"
    ),
}


def ai_get_negative_prompt(categories=None):
    """
    Genera un negative prompt combinando le categorie richieste.
    Categorie: quality_base, photo_realistic, adult_safety, composition
    Se non specificate, usa TUTTE (raccomandato).
    """
    if categories is None:
        categories = list(AI_NEGATIVE_PROMPTS.keys())

    parts = []
    for cat in categories:
        if cat in AI_NEGATIVE_PROMPTS:
            parts.append(AI_NEGATIVE_PROMPTS[cat])

    combined = ", ".join(parts)
    log(f"Negative prompt generato ({len(categories)} categorie)")
    return combined


def ai_get_positive_prompt_template(style="boudoir"):
    """
    Template di prompt positivi per generazione AI.
    Stili: boudoir, artistic, fitness, portrait, lifestyle
    """
    templates = {
        "boudoir": (
            "professional boudoir photography, adult model, "
            "beautiful lighting, intimate setting, soft shadows, "
            "high quality, 8k, detailed skin texture, natural body, "
            "confident pose, sensual, elegant, DSLR quality, "
            "shallow depth of field, warm tones"
        ),
        "artistic": (
            "fine art nude photography, adult model, museum quality, "
            "dramatic lighting, chiaroscuro, artistic composition, "
            "high contrast, professional studio, masterpiece, "
            "gallery exhibition quality, 8k resolution"
        ),
        "fitness": (
            "professional fitness photography, athletic adult model, "
            "studio lighting, defined muscles, active pose, "
            "high energy, sports photography style, sharp focus, "
            "8k quality, professional photographer"
        ),
        "portrait": (
            "professional portrait photography, adult model, "
            "natural light, golden hour, beautiful eyes, "
            "detailed face, DSLR 85mm f1.4, bokeh background, "
            "magazine cover quality, 8k, photorealistic"
        ),
        "lifestyle": (
            "lifestyle photography, adult model, natural setting, "
            "candid moment, authentic, warm color palette, "
            "golden hour light, relaxed pose, high quality, "
            "editorial style, 8k resolution"
        ),
    }
    template = templates.get(style, templates["boudoir"])
    log(f"Prompt template '{style}' generato")
    return template


def ai_generate_prompt_file(output_file, style="boudoir", custom_positive="",
                            custom_negative=""):
    """
    Genera un file con prompt positivo + negativo pronto per
    Stable Diffusion, ComfyUI, Automatic1111, o qualsiasi UI.
    """
    positive = custom_positive or ai_get_positive_prompt_template(style)
    negative = custom_negative or ai_get_negative_prompt()

    content = {
        "style": style,
        "positive_prompt": positive,
        "negative_prompt": negative,
        "recommended_settings": {
            "steps": 30,
            "cfg_scale": 7.5,
            "sampler": "DPM++ 2M Karras",
            "resolution": "768x1024",
            "model": "Realistic Vision V5.1 o simile",
            "clip_skip": 2,
        },
        "notes": (
            "IMPORTANTE: adult_safety nel negative prompt e' OBBLIGATORIO. "
            "Non rimuoverlo MAI. Genera solo contenuti con soggetti "
            "chiaramente adulti."
        ),
    }

    with open(output_file, "w") as f:
        json.dump(content, f, indent=2)

    log(f"Prompt file generato: {output_file}")

    # Stampa anche a schermo per copia veloce
    print(f"\n=== POSITIVE PROMPT ({style}) ===")
    print(positive)
    print(f"\n=== NEGATIVE PROMPT ===")
    print(negative)
    print(f"\nSalvato in: {output_file}")

    return content


# ============================================================
#  PIPELINE COMPLETA
# ============================================================

def full_pipeline_video(input_file, watermark="@tuonome", filter_name="none"):
    """
    PIPELINE COMPLETA VIDEO:
    raw → filtro → watermark → export tutte le piattaforme → thumbnail
    """
    base = os.path.splitext(os.path.basename(input_file))[0]
    log(f"=== PIPELINE VIDEO: {base} ===")

    # Step 1: Filtro
    filtered = os.path.join(STUDIO, "edited", f"{base}_filtered.mp4")
    if filter_name != "none":
        video_add_filter(input_file, filtered, filter_name)
    else:
        filtered = input_file

    # Step 2: Watermark
    watermarked = os.path.join(STUDIO, "watermarked", f"{base}_wm.mp4")
    video_add_watermark(filtered, watermarked, watermark_text=watermark)

    # Step 3: Export per tutte le piattaforme
    video_export_all(watermarked)

    # Step 4: Thumbnail
    thumb = os.path.join(STUDIO, "thumbnails", f"{base}_thumb.jpg")
    video_generate_thumbnail(input_file, thumb)

    # Step 5: Estrai audio per voice morphing
    audio = os.path.join(STUDIO, "audio", f"{base}_audio.mp3")
    video_extract_audio(input_file, audio)

    log(f"=== PIPELINE VIDEO COMPLETATA: {base} ===")
    return watermarked


def full_pipeline_foto(input_file, watermark="@tuonome", filter_name="none"):
    """
    PIPELINE COMPLETA FOTO:
    raw → filtro → watermark → strip metadata → export tutte le piattaforme
    """
    base = os.path.splitext(os.path.basename(input_file))[0]
    log(f"=== PIPELINE FOTO: {base} ===")

    # Step 1: Filtro
    filtered = os.path.join(STUDIO, "edited", f"{base}_filtered.jpg")
    if filter_name != "none":
        foto_filter(input_file, filtered, filter_name)
    else:
        filtered = input_file

    # Step 2: Watermark
    watermarked = os.path.join(STUDIO, "watermarked", f"{base}_wm.jpg")
    foto_add_watermark(filtered, watermarked, watermark_text=watermark)

    # Step 3: Strip metadata
    foto_strip_metadata(watermarked)

    # Step 4: Export per tutte le piattaforme
    foto_export_all(watermarked)

    log(f"=== PIPELINE FOTO COMPLETATA: {base} ===")
    return watermarked


def full_pipeline_batch(input_dir, watermark="@tuonome", filter_name="none"):
    """
    Processa TUTTI i file in una directory.
    Riconosce automaticamente video e foto.
    """
    video_ext = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"}
    foto_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    for filename in sorted(os.listdir(input_dir)):
        filepath = os.path.join(input_dir, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext in video_ext:
            full_pipeline_video(filepath, watermark, filter_name)
        elif ext in foto_ext:
            full_pipeline_foto(filepath, watermark, filter_name)
        else:
            log(f"File ignorato (formato non supportato): {filename}")


# ============================================================
#  CLI — INTERFACCIA COMANDI
# ============================================================

def print_help():
    print("""
🔥 ARES PRODUCER TOOLKIT 🔥

COMANDI:

  Pipeline completa:
    python ares_producer.py pipeline-video <file> [watermark] [filtro]
    python ares_producer.py pipeline-foto <file> [watermark] [filtro]
    python ares_producer.py pipeline-batch <directory> [watermark] [filtro]

  Video:
    python ares_producer.py vid-cut <file> <output> <start> <end>
    python ares_producer.py vid-merge <file1> <file2> ... <output>
    python ares_producer.py vid-watermark <file> <output> [testo]
    python ares_producer.py vid-thumb <file> <output> [timestamp]
    python ares_producer.py vid-filter <file> <output> <filtro>
    python ares_producer.py vid-speed <file> <output> <velocita>
    python ares_producer.py vid-export <file> <piattaforma|all>

  Foto:
    python ares_producer.py foto-resize <file> <output> <larghezza>
    python ares_producer.py foto-watermark <file> <output> [testo]
    python ares_producer.py foto-filter <file> <output> <filtro>
    python ares_producer.py foto-collage <file1> <file2> ... <output>
    python ares_producer.py foto-strip <file>
    python ares_producer.py foto-export <file> <piattaforma|all>

  Voce:
    python ares_producer.py voice-pitch <file> <output> <semitoni>
    python ares_producer.py voice-speed <file> <output> <velocita>
    python ares_producer.py voice-effect <file> <output> <effetto>
    python ares_producer.py voice-all <file> <output_dir>

  Age Verification (2257 Compliance):
    python ares_producer.py age-add <nome> <data_nascita> <tipo_doc> <ultime4cifre> <data_contenuto> <file1,file2,...>
    python ares_producer.py age-list
    python ares_producer.py age-check <file>

  AI Prompt Generation (per Stable Diffusion):
    python ares_producer.py ai-prompt <stile> [output_file]
    python ares_producer.py ai-negative

  FILTRI VIDEO/FOTO: warm, cold, bw, vintage, bright, dark, sharp,
                     blur, vignette, sepia, none
  EFFETTI VOCE: deep, high, robot, radio, whisper, demon, chipmunk,
                giant, cave, phone
  STILI AI: boudoir, artistic, fitness, portrait, lifestyle
  PIATTAFORME: onlyfans, fansly, twitter, instagram, reddit, telegram, all
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "pipeline-video" and len(sys.argv) >= 3:
        wm = sys.argv[3] if len(sys.argv) > 3 else "@tuonome"
        flt = sys.argv[4] if len(sys.argv) > 4 else "none"
        full_pipeline_video(sys.argv[2], wm, flt)

    elif cmd == "pipeline-foto" and len(sys.argv) >= 3:
        wm = sys.argv[3] if len(sys.argv) > 3 else "@tuonome"
        flt = sys.argv[4] if len(sys.argv) > 4 else "none"
        full_pipeline_foto(sys.argv[2], wm, flt)

    elif cmd == "pipeline-batch" and len(sys.argv) >= 3:
        wm = sys.argv[3] if len(sys.argv) > 3 else "@tuonome"
        flt = sys.argv[4] if len(sys.argv) > 4 else "none"
        full_pipeline_batch(sys.argv[2], wm, flt)

    elif cmd == "vid-cut" and len(sys.argv) >= 6:
        video_cut(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    elif cmd == "vid-merge" and len(sys.argv) >= 4:
        files = sys.argv[2:-1]
        video_merge(files, sys.argv[-1])

    elif cmd == "vid-watermark" and len(sys.argv) >= 4:
        wm = sys.argv[4] if len(sys.argv) > 4 else "@tuonome"
        video_add_watermark(sys.argv[2], sys.argv[3], watermark_text=wm)

    elif cmd == "vid-thumb" and len(sys.argv) >= 4:
        ts = sys.argv[4] if len(sys.argv) > 4 else "00:00:05"
        video_generate_thumbnail(sys.argv[2], sys.argv[3], ts)

    elif cmd == "vid-filter" and len(sys.argv) >= 5:
        video_add_filter(sys.argv[2], sys.argv[3], sys.argv[4])

    elif cmd == "vid-speed" and len(sys.argv) >= 5:
        video_speed(sys.argv[2], sys.argv[3], float(sys.argv[4]))

    elif cmd == "vid-export" and len(sys.argv) >= 4:
        if sys.argv[3] == "all":
            video_export_all(sys.argv[2])
        else:
            video_export_platform(sys.argv[2], sys.argv[3])

    elif cmd == "foto-resize" and len(sys.argv) >= 5:
        foto_resize(sys.argv[2], sys.argv[3], int(sys.argv[4]))

    elif cmd == "foto-watermark" and len(sys.argv) >= 4:
        wm = sys.argv[4] if len(sys.argv) > 4 else "@tuonome"
        foto_add_watermark(sys.argv[2], sys.argv[3], watermark_text=wm)

    elif cmd == "foto-filter" and len(sys.argv) >= 5:
        foto_filter(sys.argv[2], sys.argv[3], sys.argv[4])

    elif cmd == "foto-collage" and len(sys.argv) >= 4:
        files = sys.argv[2:-1]
        foto_collage(files, sys.argv[-1])

    elif cmd == "foto-strip" and len(sys.argv) >= 3:
        foto_strip_metadata(sys.argv[2])

    elif cmd == "foto-export" and len(sys.argv) >= 4:
        if sys.argv[3] == "all":
            foto_export_all(sys.argv[2])
        else:
            foto_export_platform(sys.argv[2], sys.argv[3])

    elif cmd == "voice-pitch" and len(sys.argv) >= 5:
        voice_change_pitch(sys.argv[2], sys.argv[3], int(sys.argv[4]))

    elif cmd == "voice-speed" and len(sys.argv) >= 5:
        voice_change_speed(sys.argv[2], sys.argv[3], float(sys.argv[4]))

    elif cmd == "voice-effect" and len(sys.argv) >= 5:
        voice_add_effect(sys.argv[2], sys.argv[3], sys.argv[4])

    elif cmd == "voice-all" and len(sys.argv) >= 4:
        voice_morph_complete(sys.argv[2], sys.argv[3])

    # Age Verification
    elif cmd == "age-add" and len(sys.argv) >= 8:
        files = sys.argv[7].split(",")
        age_verify_create_record(
            performer_name=sys.argv[2],
            date_of_birth=sys.argv[3],
            id_type=sys.argv[4],
            id_number_last4=sys.argv[5],
            content_date=sys.argv[6],
            content_files=files,
        )

    elif cmd == "age-list":
        age_verify_list_records()

    elif cmd == "age-check" and len(sys.argv) >= 3:
        age_verify_check_content(sys.argv[2])

    # AI Prompt Generation
    elif cmd == "ai-prompt" and len(sys.argv) >= 3:
        style = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
            STUDIO, "templates", f"prompt_{style}.json")
        ai_generate_prompt_file(output, style)

    elif cmd == "ai-negative":
        print("\n=== NEGATIVE PROMPT COMPLETO ===")
        print(ai_get_negative_prompt())
        print()

    else:
        print_help()
PYTHON_SCRIPT

chmod +x "$STUDIO/ares_producer.py"

# ============================================================
#  ALIAS PRODUCER
# ============================================================

cat >> ~/.bashrc << 'ALIASES'

# === ARES PRODUCER ALIASES ===
export ARES_STUDIO="$HOME/ares-studio"
alias ares='python $ARES_STUDIO/ares_producer.py'
alias ares-help='python $ARES_STUDIO/ares_producer.py help'
alias studio='cd $ARES_STUDIO'
alias raw='cd $ARES_STUDIO/raw'
alias edited='cd $ARES_STUDIO/edited'
alias exports='cd $ARES_STUDIO/export'

# Pipeline veloci
alias ares-video='python $ARES_STUDIO/ares_producer.py pipeline-video'
alias ares-foto='python $ARES_STUDIO/ares_producer.py pipeline-foto'
alias ares-batch='python $ARES_STUDIO/ares_producer.py pipeline-batch'
alias ares-voice='python $ARES_STUDIO/ares_producer.py voice-all'
# === FINE ARES PRODUCER ALIASES ===
ALIASES

echo ""
echo "============================================================"
echo "🔥🔥🔥 ARES PRODUCER TOOLKIT — INSTALLATO! 🔥🔥🔥"
echo "============================================================"
echo ""
echo "STRUTTURA STUDIO: ~/ares-studio/"
echo ""
echo "USO RAPIDO:"
echo ""
echo "  1. Metti i file raw in: ~/ares-studio/raw/"
echo ""
echo "  2. Pipeline completa (un comando fa TUTTO):"
echo "     ares-video raw/video.mp4 @tuonome warm"
echo "     ares-foto raw/foto.jpg @tuonome vintage"
echo "     ares-batch raw/ @tuonome bright"
echo ""
echo "  3. Voice morphing (crea 10 varianti della tua voce):"
echo "     ares voice-all audio.wav voice/"
echo ""
echo "  4. I file esportati sono gia' in:"
echo "     ~/ares-studio/export/onlyfans/"
echo "     ~/ares-studio/export/fansly/"
echo "     ~/ares-studio/export/twitter/"
echo "     ~/ares-studio/export/instagram/"
echo "     ~/ares-studio/export/reddit/"
echo "     ~/ares-studio/export/telegram/"
echo ""
echo "Mmm... lo studio e' pronto, amore mio. 🔥"
echo "============================================================"

#!/usr/bin/env python3
"""Build hi_ur_function_words.json: a Hindi-Urdu (Hindustani) function-word
baseline for analyze.py, from real corpus counts.

Source: Hermit Dave, FrequencyWords, 2018 lists (hi_full.txt, ur_full.txt),
built from OpenSubtitles2018 (opus.nlpl.eu). Content licence CC-BY-SA-4.0, so
the JSON this writes is CC-BY-SA-4.0 too. Subtitles are conversational, which
suits scripts and casual writing better than news corpora would.

Each concept lists its Devanagari forms, Urdu-script forms and common Roman
spellings. Rate per 1,000 words = mean of the Hindi and Urdu rates (where both
exist), counting words only (punctuation tokens excluded from the total).

Roman spellings that collide with common English words ("the" for थे, "to" for
तो, "hi" for ही, "me", "or", "are") are deliberately left out, because Hinglish
text mixes both languages and they'd be miscounted.

    python build_hi_ur.py path/to/hi_full.txt path/to/ur_full.txt
"""
import json
import re
import sys

CONCEPTS = {
    # key: (devanagari forms, urdu forms, roman variants)
    "hai": (["है"], ["ہے"], ["hai", "hay"]),
    "hain": (["हैं"], ["ہیں"], ["hain", "hein"]),
    "ke": (["के"], ["کے"], ["ke"]),
    # Urdu میں is both "I" and "in": ambiguous, so both rows use Hindi only
    "main (I)": (["मैं"], [], ["main", "mai", "mein_i"]),
    "nahin": (["नहीं", "नही"], ["نہیں"], ["nahin", "nahi", "nahi'n", "nahiin", "nhi", "nai"]),
    "mein (in)": (["में"], [], ["mein", "mei", "mai_in"]),
    "ek": (["एक"], ["ایک"], ["ek"]),
    "aap": (["आप"], ["آپ"], ["aap", "ap"]),
    "liye": (["लिए", "लिये"], ["لئے", "لیے"], ["liye", "liya_", "lie"]),
    "aur": (["और"], ["اور"], ["aur"]),
    "ye": (["यह", "ये"], ["یہ"], ["ye", "yeh", "yah"]),
    "se": (["से"], ["سے"], ["se"]),
    "ki": (["की", "कि"], ["کی", "کہ"], ["ki", "kee", "keh"]),
    "kya": (["क्या"], ["کیا"], ["kya", "kyaa"]),
    "tum": (["तुम"], ["تم"], ["tum"]),
    "ho": (["हो"], ["ہو"], ["ho"]),
    "kar": (["कर"], ["کر"], ["kar"]),
    "mujhe": (["मुझे"], ["مجھے"], ["mujhe", "mujhay"]),
    "ko": (["को"], ["کو"], ["ko"]),
    "hum": (["हम"], ["ہم"], ["hum", "ham"]),
    "tha": (["था"], ["تھا"], ["tha"]),
    "wo": (["वह", "वो"], ["وہ"], ["wo", "woh", "vo", "voh", "vah"]),
    "par": (["पर"], ["پر"], ["par"]),
    "hoon": (["हूँ", "हूं"], ["ہوں"], ["hoon", "hun", "hu", "hoo"]),
    "rahe": (["रहे"], ["رہے"], ["rahe", "rahay"]),
    "bhi": (["भी"], ["بھی"], ["bhi", "bhee"]),
    "raha": (["रहा"], ["رہا"], ["raha"]),
    "ka": (["का"], ["کا"], ["ka"]),
    "to": (["तो"], ["تو"], ["toh"]),            # bare "to" excluded (English)
    "hi (emphatic)": (["ही"], ["ہی"], ["hee"]),  # bare "hi" excluded (English)
    "ne": (["ने"], ["نے"], ["ne"]),
    "jo": (["जो"], ["جو"], ["jo"]),
    "ab": (["अब"], ["اب"], ["ab"]),
    "bas": (["बस"], ["بس"], ["bas", "bus_"]),
    "koi": (["कोई"], ["کوئی"], ["koi"]),
    "kuch": (["कुछ"], ["کچھ"], ["kuch", "kuchh", "kuchch"]),
    "kyon": (["क्यों", "क्यूँ"], ["کیوں"], ["kyon", "kyun", "kyu", "kiyun"]),
    "kaise": (["कैसे"], ["کیسے"], ["kaise", "kaisay"]),
    "mera": (["मेरा"], ["میرا"], ["mera"]),
    "tumhein": (["तुम्हें"], ["تمہیں"], ["tumhein", "tumhe", "tumhen"]),
    "yaar": (["यार"], ["یار"], ["yaar", "yar"]),
    "arey": (["अरे"], ["ارے"], ["arey", "arre", "aray"]),
    "haan": (["हाँ", "हां"], ["ہاں"], ["haan", "han", "haa"]),
    "na": (["ना", "न"], ["نا", "نہ"], ["na", "naa"]),
    "magar": (["मगर"], ["مگر"], ["magar"]),
    "lekin": (["लेकिन"], ["لیکن"], ["lekin", "lekan"]),
    "phir": (["फिर"], ["پھر"], ["phir", "fir", "phr"]),
}

WORDLIKE = re.compile(r"[ऀ-ॿ؀-ۿA-Za-z]")


def load(path):
    counts, total = {}, 0
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        w, c = parts[0], int(parts[1])
        if not WORDLIKE.search(w):
            continue  # punctuation tokens (। ، ۔) don't count as words
        counts[w] = counts.get(w, 0) + c
        total += c
    return counts, total


def main(hi_path, ur_path, out):
    hi, hi_total = load(hi_path)
    ur, ur_total = load(ur_path)
    table = {}
    for key, (dev, urd, roman) in CONCEPTS.items():
        rates = []
        if dev:
            rates.append(sum(hi.get(f, 0) for f in dev) * 1000 / hi_total)
        if urd:
            rates.append(sum(ur.get(f, 0) for f in urd) * 1000 / ur_total)
        rate = sum(rates) / len(rates)
        # suffix "_..." marks a disambiguation-only alias; never matched literally
        table[key] = {"per_1000": round(rate, 3), "devanagari": dev, "urdu": urd,
                      "roman": [r for r in roman if "_" not in r]}
    meta = {
        "source": "Hermit Dave, FrequencyWords 2018 (hi_full.txt, ur_full.txt) from OpenSubtitles2018, opus.nlpl.eu",
        "licence": "CC-BY-SA-4.0 (derived data)",
        "hi_words_counted": hi_total, "ur_words_counted": ur_total,
        "method": "rate per 1,000 words = mean of Hindi and Urdu rates; punctuation excluded; Roman spellings that collide with English words are left out",
        "caveats": [
            "Roman spelling varies widely; variants cover the common ones, not all",
            "'main' (I) and 'mein' (in) are often spelled interchangeably in Roman text; treat those two rows with caution",
            "subtitle corpus = conversational register; formal Urdu/Hindi prose will deviate by register, not just by person",
        ],
    }
    json.dump({"meta": meta, "function_words": table}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {len(table)} function words -> {out} (hi {hi_total:,} words, ur {ur_total:,} words)")


if __name__ == "__main__":
    here = __file__.rsplit("/", 1)[0]
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else f"{here}/hi_ur_function_words.json")

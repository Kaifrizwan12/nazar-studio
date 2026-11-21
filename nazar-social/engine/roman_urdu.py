#!/usr/bin/env python3
"""
nazar-social/engine/roman_urdu.py: common Roman Urdu words and their spelling variants, for the copy lint.

Roman Urdu has no standard spelling: one word is written many ways (zindagi / zindagee / zindagy), because vowels are
doubled or dropped, the "h" of an aspirate is dropped (samajh / samaj), and a final nasal "n" comes and goes (nahin / nahi).
See references/research_roman_urdu.md for the sources. So the lint must:
  1. never call a Roman Urdu word a typo (it is not misspelt English), and
  2. flag one word spelt two ways inside one piece (nahi ... nahin): pick one and keep it.
VARIANTS holds hand-checked groups, one word per group. Groups are kept narrow on purpose: words that differ in MEANING
are never merged even when a phonetic key would merge them (hai "is" / hain "are"; main_ "I" / mein "in"; kya "what" /
kiya "did", so the ambiguous "kia" sits in no group). Forms that are also everyday English words (he, me, or, ham, bad,
sub, maze, thee, hen) are left out of the groups so English is never read as Urdu. Extend a group only with a spelling
seen in real copy.
"""
import re

VARIANTS = {
    "nahi": ["nahi", "nahin", "nai", "nhi", "nahee", "nahii", "nahien"],
    "hai": ["hai", "hae", "haii"],
    "hain": ["hain", "hein", "hayn"],
    "kya": ["kya", "kyaa", "kyah"],
    "kyun": ["kyun", "kyon", "kyu", "kiun", "kyoon", "kiyon"],
    "mein": ["mein", "mien", "mei", "meyn"],
    "acha": ["acha", "achha", "accha", "achcha", "acchha", "achaa"],
    "theek": ["theek", "thik", "theik", "thek", "theekh"],
    "bhai": ["bhai", "bhaii", "bhae"],
    "yaar": ["yaar", "yar", "yaarr"],
    "karo": ["karo", "kro", "karoo"],
    "karna": ["karna", "krna", "karnaa"],
    "kuch": ["kuch", "kuchh", "kch", "kuchch"],
    "bohat": ["bohat", "bahut", "bohot", "bhot", "bht", "bohut", "bahot"],
    "abhi": ["abhi", "abi", "abhee"],
    "phir": ["phir", "fir", "phr", "pher"],
    "pehle": ["pehle", "pehlay", "pahle", "pehley", "pehly"],
    "kaise": ["kaise", "kaisay", "kaisey", "kese", "kesay", "kaisy"],
    "kaun": ["kaun", "kon", "kaon"],
    "sirf": ["sirf", "srf", "sirff"],
    "zindagi": ["zindagi", "zindagee", "zindagy", "zindgi", "zaindagee", "zndagi"],
    "khana": ["khana", "khaana", "kahana"],
    "paani": ["paani", "pani"],
    "dekho": ["dekho", "dekhoo", "dkho"],
    "wala": ["wala", "waala", "walla"],
    "wali": ["wali", "waali", "walli"],
    "gaya": ["gaya", "gya", "gayaa"],
    "raha": ["raha", "rha", "rahaa"],
    "rahe": ["rahe", "rahay", "rhe", "rahey"],
    "shukriya": ["shukriya", "shukria", "shukriyaa", "shukriyah"],
    "mazay": ["mazay", "mazey", "maze_"],
    "bilkul": ["bilkul", "bilkol", "bilkull"],
    "zaroor": ["zaroor", "zarur", "zaruur"],
    "lekin": ["lekin", "lakin", "laikin"],
    "aur": ["aur", "aor", "aurr"],
    "haan": ["haan", "han", "haa"],
    "jee": ["jee", "ji", "jii"],
    "yeh": ["yeh", "ye", "yah", "yea_"],
    "woh": ["woh", "wo", "voh", "vo"],
    "koi": ["koi", "koii", "koee"],
    "pyaar": ["pyaar", "pyar", "piyar"],
    "chai": ["chai", "chaye", "chaey", "chaai", "chae"],
    "khush": ["khush", "khus", "kush_"],
    "jaldi": ["jaldi", "jldi", "jaldee"],
    "hoga": ["hoga", "hogaa", "hogha"],
    "tha": ["tha", "thaa"],
    "baat": ["baat", "bat_"],
    "toh": ["toh", "to_"],
    "zyada": ["zyada", "ziyada", "zayada", "zeyada", "jyada"],
    "kabhi": ["kabhi", "kbhi", "kabi"],
    "sab": ["sab", "sb"],
    "apna": ["apna", "apnaa"],
    "chalo": ["chalo", "chlo", "chaloo"],
    "samajh": ["samajh", "samaj", "smjh"],
    "baaki": ["baaki", "baqi", "baki", "baqee"],
    "dobara": ["dobara", "dubara", "dobarah"],
    "matlab": ["matlab", "mtlb", "matlb"],
}
# trailing "_" marks a spelling that is also English or ambiguous: it counts as Roman Urdu only for the consistency check
# when the same piece also uses the group's main form (so "to" alone is English, "toh ... to" is flagged).

OTHER = """ka ki ko ke se par_ pe_ tak liye lie jo_ na_ ek do_ teen char_ panch kar karte karta karti kiya kia kiye ho_ hona hota
hoti hote hua hui hue tum aap ap_ hum unka unki inka inki uska uski mera meri mere tera teri tere hamara hamari tumhara
tumhari apni apne main_ mai jab_ tab_ ab yahan wahan kahan idhar udhar upar neeche andar bahar saath sath bina wapas
abhi kal_ aaj parson subah shaam raat din_ waqt time_ log_ logon dost dil_ jaan ghar dukaan bazaar sheher gaon mulk
khana peena dekh dekhna dekhte suno sunna bolo bolna batao bata chal chalna chalte jao jana aao aana lo_ lena do_ dena
rakh rakho rakhna socho sochna samjho pata maloom yaad bhool bhoolna pehla pehli doosra doosri aakhri naya nayi naye
purana purani acchi achi ache bura buri bure bara bari bare chota choti chote zara thora thoda thori thodi bas_
sahi galat asli naqli sasta mehnga mazedaar mazay maza khaas aam sirf bhi hi_ jee haan ji wah waah arey arre oye
shabash mubarak inshallah mashallah bismillah salaam assalam alaikum khuda hafiz allah shukar sukoon izzat
bhook pyaas garam thanda meetha namkeen khatta teekha chatpata desi pakka kacha kaccha chalega chalegi karega karegi
hoga hogi honge karenge dekhenge milenge milega milegi mil_ milna milte wala wali wale walay karo karna karein kijiye
dijiye lijiye aaiye jaiye baithiye suniye dekhiye batayein pehle phir baad baaki verify_ share_""".split()

_LOOKUP = {}
for head, forms in VARIANTS.items():
    for f in forms:
        _LOOKUP.setdefault(f.rstrip("_").lower(), (head, f.endswith("_")))
WORDS = set(_LOOKUP) | {w.rstrip("_").lower() for w in OTHER if not w.endswith("_")}
WORD_RE = re.compile(r"[A-Za-z']+")


def tokens(text):
    return [w.lower().strip("'") for w in WORD_RE.findall(text) if w.strip("'")]


def is_roman_urdu(word):
    w = word.lower()
    return w in WORDS and not _LOOKUP.get(w, ("", False))[1]


def share(text):
    t = tokens(text)
    return round(sum(is_roman_urdu(w) for w in t) / len(t), 2) if t else 0.0


def inconsistent(text):
    """[(head, {spelling: count})] for each word spelt two or more ways in this text."""
    seen = {}
    for w in tokens(text):
        if w in _LOOKUP:
            head, amb = _LOOKUP[w]
            seen.setdefault(head, {}).setdefault(w, [0, amb])[0] += 1
    out = []
    for head, forms in seen.items():
        clear = {f: c for f, (c, amb) in forms.items() if not amb}
        if len(forms) >= 2 and clear:              # an ambiguous form counts only next to_ a clear Roman Urdu form
            out.append((head, {f: c for f, (c, _) in forms.items()}))
    return out

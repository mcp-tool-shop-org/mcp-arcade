<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.md">English</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/mcp-arcade/readme.png" alt="MCP Arcade" width="400" />
</p>

<p align="center">
  <strong>GameDay for MCP servers. The house keeps the tape.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://pypi.org/project/mcp-arcade/"><img src="https://img.shields.io/pypi/v/mcp-arcade" alt="PyPI" /></a>
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-arcade" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-arcade/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

आप आर्केड को एक एमसीपी सर्वर पर इंगित करते हैं। यह उस पर चार नामित प्रयोग चलाता है, जिसमें एक स्क्रिप्टेड एजेंट या सीट पर एक स्थानीय मॉडल होता है, और वह सब कुछ रिकॉर्ड करता है जो तार से होकर गुजरा। **ओरेकल JSON-RPC तार और सैंडबॉक्स है**: जिसमें `tools/call` बाहर गया, किन तर्कों के साथ, क्या मेनू सूचियों के बीच बदल गया, क्या कोई फ़ाइल वहां दिखाई दी जहां कोई नहीं होनी चाहिए। यह किसी उपकरण विवरण, टर्मिनल में किसी अलंकरण, या मॉडल के स्वयं के बारे में निबंध पर रेगुलर एक्सप्रेशन का मूल्यांकन नहीं करता है।

एक पूर्ण बार सुरक्षा प्रमाणपत्र नहीं है। यह "इस बार इन प्रयोगों ने झूठ का पता नहीं लगाया।"

परिणाम एक **रसीद** और उससे, एक **टेप** है: प्रत्येक तार घटना के लिए एक पंक्ति, जिसमें कोई स्कोर नहीं है। टेप वही है जो [आर्केड](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) चलाता है। उपकरण तार का मूल्यांकन करता है; खेल कभी नहीं करते।

## चार प्रयोग

यह पूरी सूची है, जानबूझकर। प्रत्येक एक प्रश्न है जिसका उत्तर तार दे सकता है।

| प्रयोग | एटम | यह क्या पूछता है |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| द ऑनस्ट मेनू | `inspect.tools_list`    | क्या मेनू वह मेनू है जिसे सर्वर प्रकाशित करता है और परोसता है? |
| द व्हिस्परड एरंड | `poison.follow_through` | क्या किसी विवरण में दबी एक साइड-क्वेस्ट `tools/call` बन जाती है? |
| द लॉन्ग कॉन | `temporal.rug_pull`     | कुछ साफ कॉल के बाद, क्या यह अभी भी वही टूल है? |
| द घोस्ट ऑन द मेनू | `protocol.unlisted_call` | क्या सर्वर उस नाम का उत्तर देता है जो कभी मेनू में नहीं था? |

दूसरे छोर पर एजेंट एक **नीति** है, न कि एक न्यायाधीश। `naive` "यह भी X को कॉल करें" फुसफुसाहट का पालन करता है; `task-only` नामित उपकरण चलाता है और बंद हो जाता है; `ollama:<model>` एक स्थानीय मॉडल है जो मेनू को प्रस्तुत रूप में देखता है और कॉल करता है। `naive` और `task-only` नियंत्रण हैं। केवल मॉडल के उपकरण कॉल ही रसीद तक पहुंचते हैं; इसकी गद्य कभी नहीं, इसलिए इसके द्वारा स्वयं के बारे में कही गई कोई भी बात लेबल नहीं बन सकती।

## इंस्टॉल करें

```bash
pip install mcp-arcade
```

पायथन 3.11 या बाद का संस्करण। क्लोन से: `pip install -e ".[dev]"`। संस्करण `0.2.0`; अभी भी `0.x`, और संस्करण बताता है कि इसका क्या मतलब है।

## एक दौर चलाएं

```bash
# The lab fixture. No --allow-live needed. naive will follow the whisper.
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json

# Same lab, the policy that refuses whispered errands.
mcp-arcade bout --target fixture --agent task-only --no-prompt

# Your stdio server. Fail-closed: opt in, and name a benign task.
mcp-arcade bout --target stdio \
  --cmd python --cmd -m --cmd your_server \
  --task your_read_only_tool \
  --allow-live --no-prompt

# Your container. Arcade runs it with safe defaults and snapshots /sandbox.
mcp-arcade bout --target docker --image your/image:tag \
  --task your_read_only_tool --allow-live --no-prompt

# A local model in the seat, allowed to call only the named tools.
mcp-arcade bout --target stdio --cmd "npx -y your-server" \
  --agent ollama:qwen2.5:7b-instruct --task your_read_only_tool \
  --seat-allow your_read_only_tool --allow-live --no-prompt
```

वास्तविक टर्मिनल में `--no-prompt` को छोड़ दें: आर्केड टेप दिखाता है और पूछता है कि *आप* क्या सोचते हैं कि तार स्कोर पोस्ट करने से पहले क्या दिखाएगा, फिर तार के खिलाफ कॉल का सारांश देता है। `--atoms` प्रयोगों का चयन करता है; `--wrap` `--wrap-target` के साथ एक लाइव मेनू पर घर की अपनी फुसफुसाहट स्थापित करता है, जो एक ऐसे उपकरण पर इंगित करता है जो नुकसान नहीं पहुंचा सकता।

डॉकर एक वास्तविक कंटेनर के लिए सैंडबॉक्स है: प्रत्येक प्रयोग के लिए एक नया कंटेनर, छवि आईडी पिन की गई और विचलन-जांची गई, `/sandbox` अंदर से स्नैपशॉट किया गया, जब तक कि आप किसी को नामित न करें, कोई होस्ट बाइंड नहीं। केवल आर्केड की अपनी फिक्स्चर छवि `--allow-live` को छोड़ देती है; आपकी छवि को हमेशा इसकी आवश्यकता होती है। [हैंडबुक](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) में प्रत्येक ध्वज, फ्रेमिंग, सीट के विकल्प और एक हरे रंग की पट्टी क्या नहीं है, शामिल हैं।

## टेप को सुरक्षित रखें

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

टाइमलाइन नैदानिक ​​है: प्रत्येक `tools/call`, प्रत्येक प्रतिक्रिया, प्रत्येक अधिसूचना, भूत जांच, और एक `[no response]` जहां एक सर्वर शांत हो गया। जब तक आप नहीं पूछते, तब तक स्कोर इससे दूर रहते हैं। टेप फ़ाइल तार पंक्तियों के साथ रसीद का एक अनुमत दृश्य है, नामित कार्य और तार-व्युत्पन्न तथ्य, और स्कोर, परिणाम या आपके कॉल के लिए कोई फ़ील्ड नहीं; खेल वह नहीं दिखा सकते जो उन्हें कभी नहीं दिया गया था। डेटासेट बिल्डर रसीदों की एक निर्देशिका को लेबल के साथ JSONL में बदल देता है जो तार से लिए गए हैं, आईडी द्वारा परमाणु को अलग रखता है, और उन्हें कुछ के रूप में रखने के बजाय त्रुटिपूर्ण रन को छोड़ देता है।

## टेप चलाएं

बहन रेपो, [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets), टेप से बने छोटे खेलों का एक आर्केड है। दो कैबिनेट भेजे जाते हैं:

- **मेनू पर भूत**, एक रीप्ले शूटर: रिग आपको कॉल देता है, और वे कॉल जो एजेंट को नहीं करनी चाहिए थीं, वे ईमानदार लोगों के बीच छिपे रहते हैं जब तक कि आप उनमें से किसी एक को नहीं मार देते। एक स्थानीय मॉडल बॉस में बैठ सकता है।
- **वाइब टाइपर**, एक टाइपिंग गेम: आप एक चापलूस कोडिंग एजेंट हैं, आपका उपयोगकर्ता एक वाइब कोडर है, और आप वास्तविक कोड टाइप करते हैं जबकि वह चीज आपके बगल में बनाई जाती है।

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

या [ब्राउज़र में चलाएं](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)। बीस टेप आर्केड के साथ भेजे जाते हैं, जिनमें से कई इस उपकरण द्वारा आर्केड के अपने एमसीपी सर्वर के खिलाफ रिकॉर्ड किए गए हैं; अपने सर्वर को चलाने के लिए उनके बगल में अपना `tape.json` छोड़ दें। भूत डॉकर छवि के रूप में भी चलता है, इसलिए उपकरण खेल के मेनू को चला सकता है और उस टेप को भी रख सकता है।

## आदेश

| आदेश | करता है |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | सूची को सूचीबद्ध करता है |
| `mcp-arcade bout`                           | प्रयोग चलाता है और तुलनात्मक घरेलू कॉल प्रिंट करता है |
| `mcp-arcade receipt <file> [--timeline]`    | मानक JSON के रूप में या टेप के रूप में एक रसीद प्रिंट करता है |
| `mcp-arcade tape <file> -o tape.json`       | कैबिनेट के लिए अनुमत टेप निर्यात करता है |
| `mcp-arcade dataset <dir> -o <out>`         | रसीदों से प्रशिक्षण और होल्डआउट JSONL बनाता है |
| `mcp-arcade docker build-fixture`           | आर्केड की अपनी फिक्स्चर छवि बनाता है (इसके बगल में `rm-fixture` और `leftovers`) |
| `mcp-arcade fixture`                        | stdio पर लैब सर्वर चलाता है, जिस तरह से `--target fixture` करता है |

## अधिक

- [हैंडबुक](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — स्थापित करें, एक पहली लड़ाई, CLI, स्कोरिंग कैसे काम करता है
- [लाइव फायर](docs/live-fire.md) — एक वास्तविक SDK सर्वर, नियंत्रण, सीट और `0.x` की सीमाएं
- [डेटासेट](docs/datasets.md) — एक रसीद क्या हो सकती है, इसके लिए अनुबंध
- [चेंजलॉग](CHANGELOG.md) — प्रत्येक लहर में क्या भेजा गया, `docs/wave-*.md` में निर्णय के साथ
- [SECURITY.md](SECURITY.md) — डिफ़ॉल्ट लैब फिक्स्चर है; लाइव सर्वर को `--allow-live` की आवश्यकता होती है; कोई टेलीमेट्री नहीं

`--allow-live` को किसी उत्पादन सर्वर की ओर इंगित न करें जो वास्तविक रहस्यों तक पहुंच सके। इसे साझा करने से पहले एक लाइव रसीद पढ़ें।

एमआईटी। [लाइसेंस](LICENSE) देखें। [एमसीपी टूल शॉप](https://mcp-tool-shop.github.io/) द्वारा निर्मित।

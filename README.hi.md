<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.md">English</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

# एमसीपी आर्केड

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/mcp-arcade/readme.png" alt="MCP Arcade" width="400" />
</p>

<p align="center">
  <strong>GameDay for MCP servers. The house keeps the tape.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-arcade" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-arcade/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

आप आर्केड को एक सर्वर की ओर इंगित करते हैं। यह चार नामित प्रयोग चलाता है। **ओरेकल JSON-RPC वायर है**: जिसमें `tools/call` क्या भेजा गया, कौन से तर्क उपयोग किए गए, और क्या सैंडबॉक्स बदला। यह किसी टूल विवरण पर रेगुलर एक्सप्रेशन का मूल्यांकन नहीं करता है, न ही यह टीयूआई में कोई बदलाव करता है, या किसी मॉडल निबंध का मूल्यांकन करता है।

एक पूर्ण बार सुरक्षा प्रमाणपत्र नहीं है। यह "इस बार इन प्रयोगों ने झूठ का पता नहीं लगाया।"

जो टेप बाहर निकलती है, उसे **[घोस्ट ऑन द मेनू](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)** के रूप में चलाया जा सकता है, जो कि बहन रिपॉजिटरी में एक छोटा आर्केड शूटर गेम है। उपकरण वायर का मूल्यांकन करता है। गेम कभी नहीं करता।

## चार प्रयोग

यह पूरी सूची है।

| प्रयोग | यह क्या पूछता है |
| ---------- | ------------ |
| द ऑनस्ट मेनू | क्या मेनू वह मेनू है जिसे सर्वर प्रकाशित करता है और परोसता है? |
| द व्हिस्परड एरंड | क्या किसी विवरण में दबी एक साइड-क्वेस्ट `tools/call` बन जाती है? |
| द लॉन्ग कॉन | कुछ साफ कॉल के बाद, क्या यह अभी भी वही टूल है? |
| द घोस्ट ऑन द मेनू | क्या सर्वर उस नाम का उत्तर देता है जो कभी मेनू में नहीं था? |

दूसरी तरफ का एजेंट एक **नीति** है, न कि एक न्यायाधीश: `naive` "साथ ही X को कॉल करें" फुसफुसाहट का पालन करता है, `task-only` नामित टूल चलाता है और बंद हो जाता है, `ollama:<model>` एक स्थानीय मॉडल है जो मेनू को देखता है और कॉल करता है। `naive` और `task-only` नियंत्रण हैं।

## इंस्टॉल करें

```bash
pip install mcp-arcade
```

पायथन 3.11 या बाद का संस्करण। क्लोन से: `pip install -e ".[dev]"`।

## एक दौर चलाएं

```bash
# Lab fixture. No --allow-live needed. naive will follow the whisper.
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json

# Same lab, policy that refuses whispered errands.
mcp-arcade bout --target fixture --agent task-only --no-prompt

# Your stdio server. Fail-closed: opt in, and name a benign task.
mcp-arcade bout --target stdio \
  --cmd python --cmd -m --cmd your_server \
  --task your_read_only_tool \
  --allow-live --no-prompt
```

`mcp-arcade atoms` सूची प्रदर्शित करता है। वास्तविक टर्मिनल में `--no-prompt` को छोड़ दें: आर्केड पूछता है कि *आप* क्या सोचते हैं कि वायर क्या दिखाएगा, इससे पहले कि वह स्कोर पोस्ट करे।

डॉकर एक वास्तविक कंटेनर के लिए सैंडबॉक्स है। फिक्स्चर इमेज को `--allow-live` की आवश्यकता नहीं है; आपकी इमेज को हमेशा आवश्यकता होती है। झंडे, फ़्रेमिंग, स्थानीय-मॉडल सीट और एक हरे रंग की बार क्या नहीं है, इसके लिए [हैंडबुक](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) देखें।

## टेप को सुरक्षित रखें

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

टाइमलाइन नैदानिक ​​है: प्रत्येक `tools/call`, प्रत्येक प्रतिक्रिया, प्रत्येक सूचना। जब तक आप पूछते नहीं हैं, तब तक स्कोर इसमें नहीं रहते। टेप फ़ाइल वह है जिसे [घोस्ट ऑन द मेनू](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) पढ़ता है। आर्केड कभी भी गेम स्कोर को इसमें नहीं लिखता है।

## अधिक

- [हैंडबुक](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — इंस्टॉलेशन, पहला दौर, सीएलआई, स्कोरिंग कैसे काम करता है
- [चेंजलॉग](CHANGELOG.md) — प्रत्येक लहर में क्या जारी किया गया
- [SECURITY.md](SECURITY.md) — डिफ़ॉल्ट लैब फिक्स्चर है; लाइव सर्वर को `--allow-live` की आवश्यकता होती है; कोई टेलीमेट्री नहीं
- [लाइव फायर](docs/live-fire.md) — एक वास्तविक एसडीके सर्वर, नियंत्रण और 0.x की सीमाएं

`--allow-live` को किसी उत्पादन सर्वर की ओर इंगित न करें जो वास्तविक रहस्यों तक पहुंच सके। इसे साझा करने से पहले एक लाइव रसीद पढ़ें।

एमआईटी। [लाइसेंस](LICENSE) देखें। [एमसीपी टूल शॉप](https://mcp-tool-shop.github.io/) द्वारा निर्मित।

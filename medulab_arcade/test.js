
    const contents = x;
    const contentType = "x";
    const lang = "x";
    let inputLang = 'x';
    let hintLang = inputLang === 'ko' ? 'en' : 'ko';
    
    let currentIndex = 0;
    let completedCount = 0;
    let completedStrokes = 0;
    let totalErrors = 0;
    let totalChars = 0;
    let startTime = null; // ?ÑÏ≤¥ ?∞Ïäµ ?úÏûë (Ï≤????ÖÎ†• ?ÑÏö©)
    let itemStartTime = null; // ?ÑÏû¨ ?®Ïñ¥/Î¨∏Ïû• ?ÖÎ†• ?úÏûë
    let cumulativeTime = 0; // ?§Ï†ú ?ÖÎ†•???åÏöî???ÑÏ†Å ?úÍ∞Ñ (ms)
    let maxWpm = 0;
    let soundEnabled = localStorage.getItem('typingSound') === 'on';
    let showHands = localStorage.getItem('showHands') !== 'off';
    let ttsRates = JSON.parse(localStorage.getItem('ttsRates') || '{"ko":"1.0", "en":"0.3", "ja":"1.0", "zh":"1.0"}');
    const inputField = document.getElementById('typing-input');
    const targetTextContainer = document.getElementById('target-text'); // ?¥Î¶Ñ Ï§ëÎ≥µ Î∞©Ï?

    function updateTTSRate(rate) {
        ttsRates[inputLang] = rate;
        localStorage.setItem('ttsRates', JSON.stringify(ttsRates));
    }

    function initTTSRateSelect() {
        const select = document.getElementById('tts-rate-select');
        select.value = ttsRates[inputLang] || '1.0';
    }

    // [v15] ?§Î≥¥???∞Ïù¥??Î∞??∏Îìú Í∞Ä?¥Îìú Î°úÏßÅ ?¥Ïãù
    const KEYBOARD_LAYOUT_DATA = [
        [
            {k:'`', c:'Backquote', s:'~'}, {k:'1', c:'Digit1', s:'!'}, {k:'2', c:'Digit2', s:'@'}, {k:'3', c:'Digit3', s:'#'}, {k:'4', c:'Digit4', s:'$'}, {k:'5', c:'Digit5', s:'%'}, {k:'6', c:'Digit6', s:'^'}, {k:'7', c:'Digit7', s:'&'}, {k:'8', c:'Digit8', s:'*'}, {k:'9', c:'Digit9', s:'('}, {k:'0', c:'Digit0', s:')'}, {k:'-', c:'Minus', s:'_'}, {k:'=', c:'Equal', s:'+'}, {k:'Backspace', c:'Backspace', w:'w-back'}
        ],
        [
            {k:'Tab', c:'Tab', w:'w-tab'}, {k:'Q', c:'KeyQ', ko:'??, koS:'??}, {k:'W', c:'KeyW', ko:'??, koS:'??}, {k:'E', c:'KeyE', ko:'??, koS:'??}, {k:'R', c:'KeyR', ko:'??, koS:'??}, {k:'T', c:'KeyT', ko:'??, koS:'??}, {k:'Y', c:'KeyY', ko:'??}, {k:'U', c:'KeyU', ko:'??}, {k:'I', c:'KeyI', ko:'??}, {k:'O', c:'KeyO', ko:'??, koS:'??}, {k:'P', c:'KeyP', ko:'??, koS:'??}, {k:'[', c:'BracketLeft', s:'{'}, {k:']', c:'BracketRight', s:'}'}, {k:'\\', c:'Backslash'}
        ],
        [
            {k:'Caps', c:'CapsLock', w:'w-caps'}, {k:'A', c:'KeyA', ko:'??}, {k:'S', c:'KeyS', ko:'??}, {k:'D', c:'KeyD', ko:'??}, {k:'F', c:'KeyF', ko:'??}, {k:'G', c:'KeyG', ko:'??}, {k:'H', c:'KeyH', ko:'??}, {k:'J', c:'KeyJ', ko:'??}, {k:'K', c:'KeyK', ko:'??}, {k:'L', c:'KeyL', ko:'??}, {k:';', c:'Semicolon', s:':'}, {k:"'", c:'Quote', s:'"'}, {k:'Enter', c:'Enter', w:'w-enter'}
        ],
        [
            {k:'Shift', c:'ShiftLeft', w:'w-shift-l'}, {k:'Z', c:'KeyZ', ko:'??}, {k:'X', c:'KeyX', ko:'??}, {k:'C', c:'KeyC', ko:'??}, {k:'V', c:'KeyV', ko:'??}, {k:'B', c:'KeyB', ko:'??}, {k:'N', c:'KeyN', ko:'??}, {k:'M', c:'KeyM', ko:'??}, {k:',', c:'Comma', s:'<'}, {k:'.', c:'Period', s:'>'}, {k:'/', c:'Slash', s:'?'}, {k:'Shift', c:'ShiftRight', w:'w-shift-r'}
        ],
        [{k:'Ctrl', c:'ControlLeft', w:'w-ctrl'}, {k:'Alt', c:'AltLeft'}, {k:'Space', c:'Space', w:'w-space'}, {k:'Alt', c:'AltRight'}, {k:'Ctrl', c:'ControlRight', w:'w-ctrl'}]
    ];

    const FINGER_MAP = {
        'L5': ['`','1','Q','A','Z','Tab','CapsLock','ShiftLeft','??,'??,'??,'ControlLeft'],
        'L4': ['2','W','S','X','??,'??,'??],
        'L3': ['3','E','D','C','??,'??,'??],
        'L2': ['4','5','R','T','F','G','V','B','??,'??,'??,'??,'??,'??],
        'L1': ['Space'], 'R1': ['Space'],
        'R2': ['6','7','Y','U','H','J','N','M','??,'??,'??,'??,'??,'??],
        'R3': ['8','I','K',',','??,'??],
        'R4': ['9','O','L','.','??,'??],
        'R5': ['0','-','=','P','[',']','\\',';','\'','/','Enter','ShiftRight','??, 'Backspace']
    };

    function decomposeKo(text) {
        if (!text) return [];
        const CHO_MAP = ['??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??];
        const JUNG_MAP = ['??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??];
        const JONG_MAP = ['', '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '?Ä', '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '??];
        const JUNG_DECOMP = {'??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??]};
        const JONG_DECOMP = {'??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '??:['??,'??], '?Ä':['??,'??], '??:['??,'??]};
        
        let strokes = [];
        for (let i=0; i<text.length; i++) {
            const char = text[i];
            const code = char.charCodeAt(0);
            if (code >= 0xAC00 && code <= 0xD7A3) { // ?úÍ? ?åÏ†à
                const index = code - 0xAC00;
                const cho = CHO_MAP[Math.floor(index / 588)];
                const jung = JUNG_MAP[Math.floor((index % 588) / 28)];
                const jong = JONG_MAP[index % 28];
                strokes.push(cho);
                if (JUNG_DECOMP[jung]) strokes.push(...JUNG_DECOMP[jung]);
                else strokes.push(jung);
                if (jong) {
                    if (JONG_DECOMP[jong]) strokes.push(...JONG_DECOMP[jong]);
                    else strokes.push(jong);
                }
            } else if (code >= 0x3131 && code <= 0x3163) { // ?úÍ? ?êÎ™®
                if (JONG_DECOMP[char]) strokes.push(...JONG_DECOMP[char]);
                else if (JUNG_DECOMP[char]) strokes.push(...JUNG_DECOMP[char]);
                else strokes.push(char);
            } else {
                strokes.push(char); // ?åÌååÎ≤? ?´Ïûê, ?πÏàòÍ∏∞Ìò∏
            }
        }
        return strokes;
    }

    const SHIFT_MAP = {
        '??:'??,'??:'??,'??:'??,'??:'??,'??:'??,'??:'??,'??:'??,'Q':'??,'W':'??,'E':'??,'R':'??,'T':'??,'O':'??,'P':'??,'!':'1','@':'2','#':'3','$':'4','%':'5','^':'6','&':'7','*':'8','(':'9',')':'0','_':'-','+':'=','~':'`','{':'[','}':']','|':'\\',':':';','"':'\'','<':',','>':'.','?':'/',' ':'Space'
    };

    const CHAR_TO_CODE = {
        '`':'Backquote','1':'Digit1','2':'Digit2','3':'Digit3','4':'Digit4','5':'Digit5','6':'Digit6','7':'Digit7','8':'Digit8','9':'Digit9','0':'Digit0','-':'Minus','=':'Equal','[':'BracketLeft',']':'BracketRight','\\':'Backslash',';':'Semicolon',"'":'Quote',',':'Comma','.':'Period','/':'Slash','Space':'Space','Enter':'Enter','Tab':'Tab'
    };

    let showHands = localStorage.getItem('showHands') !== 'off';

    function getKeyEl(char) {
        if (!char) return null;
        if (CHAR_TO_CODE[char]) return document.getElementById(`key-${CHAR_TO_CODE[char]}`);
        const el = document.getElementById(`key-${char}`) || document.getElementById(`key-${char.toUpperCase()}`);
        if (el) return el;
        if (char.length === 1 && /[a-zA-Z]/.test(char)) return document.getElementById(`key-Key${char.toUpperCase()}`);
        return null;
    }

    function initKeyboard() {
        const kb = document.getElementById('v-keyboard');
        if (!kb) return;
        kb.innerHTML = '';
        KEYBOARD_LAYOUT_DATA.forEach((row, idx) => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'key-row';
            if (idx === 1) rowDiv.style.marginLeft = '15px';
            if (idx === 2) rowDiv.style.marginLeft = '35px';
            if (idx === 3) rowDiv.style.marginLeft = '60px';
            row.forEach(item => {
                const keyDiv = document.createElement('div');
                keyDiv.className = `key ${item.w || ''}`;
                let keyId = item.c || item.k;
                if (inputLang === 'ko' && item.ko) keyId = item.ko;
                keyDiv.id = `key-${keyId}`;
                let shiftCharHTML = '';
                let shiftChar = item.s || '';
                if (inputLang === 'ko' && item.koS) shiftChar = item.koS;
                
                if (shiftChar) {
                    shiftCharHTML = `<span style="font-size:10.5px; color:#94a3b8; position:absolute; top:4px; right:6px; font-weight:800;">${shiftChar}</span>`;
                }

                if (inputLang === 'ko' && item.ko) {
                    keyDiv.innerHTML = `<span style="font-size:10.5px; color:#64748b; position:absolute; top:4px; left:6px; font-weight:800;">${item.k}</span>${shiftCharHTML}<span style="font-weight:900; margin-top:8px;">${item.ko}</span>`;
                } else if (item.k.length === 1) { // Numbers and letters
                    keyDiv.innerHTML = `${shiftCharHTML}<span style="font-weight:900; margin-top:${shiftChar ? '8px' : '0'};">${item.k}</span>`;
                } else {
                    keyDiv.innerText = item.k;
                }
                rowDiv.appendChild(keyDiv);
            });
            kb.appendChild(rowDiv);
        });
        applyHandToggle();
        setTimeout(setDefaultHandPositions, 100);
    }

    function positionHand(handEl, fingerId, keyEl, wrapRect, stateClass) {
        const tipEl = document.getElementById(`tip-${fingerId}`);
        if (!tipEl || !keyEl || !wrapRect) return;
        const keyRect = keyEl.getBoundingClientRect();
        const keyTop = keyRect.top - wrapRect.top + keyRect.height / 2;
        const keyLeft = keyRect.left - wrapRect.left + keyRect.width / 2;
        const tipX = tipEl.cx.baseVal.value;
        const tipY = tipEl.cy.baseVal.value;
        const scale = 460 / 200;
        handEl.style.top = `${keyTop - tipY * scale - 15}px`;
        handEl.style.left = `${keyLeft - tipX * scale}px`;
        handEl.style.transform = 'none';
        handEl.classList.remove('active', 'rest', 'home');
        if (stateClass) handEl.classList.add(stateClass);
    }

    function setDefaultHandPositions() {
        const wrap = document.querySelector('.keyboard-wrapper');
        if (!wrap) return;
        const wrapRect = wrap.getBoundingClientRect();
        const leftHomeEl = inputLang === 'ko' ? document.getElementById('key-??) : document.getElementById('key-KeyF');
        const rightHomeEl = inputLang === 'ko' ? document.getElementById('key-??) : document.getElementById('key-KeyJ');
        if (leftHomeEl) positionHand(document.getElementById('hand-left'), 'L2', leftHomeEl, wrapRect, 'home');
        if (rightHomeEl) positionHand(document.getElementById('hand-right'), 'R2', rightHomeEl, wrapRect, 'home');
    }

    function updateHandToChar(chars) {
        if (!showHands || !chars) return;
        document.querySelectorAll('.key').forEach(k => k.classList.remove('target'));
        document.querySelectorAll('.finger-group').forEach(f => f.classList.remove('striking'));
        
        const handLeft = document.getElementById('hand-left');
        const handRight = document.getElementById('hand-right');
        let charArray = Array.isArray(chars) ? chars : [chars];
        
        charArray.forEach(char => {
            let lookupChar = char;
            let isShiftRequired = false;
            
            if (SHIFT_MAP[char]) {
                lookupChar = SHIFT_MAP[char];
                isShiftRequired = (char !== ' ' && char !== lookupChar);
            }
            
            const targetDiv = getKeyEl(lookupChar);
            if (targetDiv) {
                targetDiv.classList.add('target');
                let targetFinger = '';
                for (const [fId, keys] of Object.entries(FINGER_MAP)) {
                    if (keys.includes(lookupChar) || (lookupChar.length === 1 && keys.includes(lookupChar.toUpperCase()))) {
                        targetFinger = fId; break;
                    }
                }
                
                if (targetFinger) {
                    const isLeftMain = targetFinger.startsWith('L');
                    const wrap = document.querySelector('.keyboard-wrapper');
                    const wrapRect = wrap.getBoundingClientRect();
                    document.getElementById(`finger-${targetFinger}`)?.classList.add('striking');
                    positionHand(isLeftMain ? handLeft : handRight, targetFinger, targetDiv, wrapRect, 'active');
                    
                    if (isShiftRequired) {
                        const shiftHand = isLeftMain ? handRight : handLeft;
                        const shiftFinger = isLeftMain ? 'R5' : 'L5';
                        const shiftKeyId = isLeftMain ? 'key-ShiftRight' : 'key-ShiftLeft';
                        const shiftKeyEl = document.getElementById(shiftKeyId);
                        if (shiftKeyEl) {
                            document.getElementById(`finger-${shiftFinger}`)?.classList.add('striking');
                            positionHand(shiftHand, shiftFinger, shiftKeyEl, wrapRect, 'active');
                        }
                    }
                }
            }
        });
    }

    function toggleHands() {
        showHands = !showHands;
        localStorage.setItem('showHands', showHands ? 'on' : 'off');
        applyHandToggle();
    }

    function applyHandToggle() {
        const wrap = document.querySelector('.hand-overlay-container');
        const btn = document.getElementById('hand-toggle-btn');
        const status = document.getElementById('hand-toggle-status');
        if (wrap) wrap.style.display = showHands ? 'block' : 'none';
        if (btn) btn.classList.toggle('off', !showHands);
        if (status) status.innerText = showHands ? 'ON' : 'OFF';
        if (showHands) setTimeout(setDefaultHandPositions, 150);
    }

    function getStrokeCount(text) {
        if (!text) return 0;
        let count = 0;
        for (let i = 0; i < text.length; i++) {
            const code = text.charCodeAt(i);
            if (code >= 0xAC00 && code <= 0xD7A3) { // ?úÍ? ?åÏ†à
                const index = code - 0xAC00;
                const cho = Math.floor(index / 588);
                const jung = Math.floor((index % 588) / 28);
                const jong = index % 28;
                let c = 2; // Ï¥àÏÑ± + Ï§ëÏÑ±
                if (jong > 0) c += 1;
                if ([1, 4, 8, 10, 13].includes(cho)) c += 1;
                if ([9, 10, 11, 14, 15, 16, 19].includes(jung)) c += 1;
                if ([2, 4, 5, 9, 10, 11, 12, 13, 14, 15, 18].includes(jong)) c += 1;
                count += c;
            } else if (code >= 0x3131 && code <= 0x3163) { // ?±Ïûê
                count += 1;
            } else {
                count += 1;
            }
        }
        return count;
    }

    function init() {
        updateSoundIcon();
        initKeyboard(); 
        
        if (contents.length === 0) {
            if (targetTextContainer) targetTextContainer.innerText = "?∞Ïäµ ?∞Ïù¥?∞Í? ?ÜÏäµ?àÎã§.";
            inputField.disabled = true;
            return;
        }
        
        if (contentType === 'word') {
            contents.sort(() => Math.random() - 0.5);
        }
        
        const limit = contentType === 'word' ? 30 : 15;
        if (contents.length > limit) {
            contents.splice(limit);
        }
        
        updateTarget();
        updateStatus();
        inputField.focus();
    }

    // Ï¥àÍ∏∞ ?§Ï†ï


    // Ï¥àÍ∏∞ ?úÎ°≠?§Ïö¥ ?§Ï†ï
    document.getElementById('input-lang').value = inputLang;
    document.getElementById('hint-lang').value = hintLang;

    function changeInputLang(val) {
        inputLang = val;
        // ?∞Ïäµ ?∏Ïñ¥???∞Î•∏ Î≤àÏó≠ ?∏Ïñ¥ ?êÎèô Ï∂îÏ≤ú Î°úÏßÅ
        const hintSelect = document.getElementById('hint-lang');
        if (inputLang === 'ko') {
            hintLang = 'en';
        } else {
            hintLang = 'ko';
        }
        hintSelect.value = hintLang;
        
        document.getElementById('tts-rate-select').value = ttsRates[inputLang] || '1.0';
        
        updateTarget();
        updateStatus();
        inputField.focus();
    }

    function changeHintLang(val) {
        hintLang = val;
        updateTarget();
        inputField.focus();
    }

    function updateTarget() {
        if (currentIndex < contents.length) {
            const currentData = contents[currentIndex];
            const targetTextStr = currentData[inputLang] || currentData['ko'] || '?∞Ïù¥???ÜÏùå';
            
            targetTextContainer.innerText = targetTextStr;
            
            // ?¥Ï†Ñ/?§Ïùå ?çÏä§???úÏãú
            document.getElementById('prev-text').innerText = currentIndex > 0 ? (contents[currentIndex-1][inputLang] || contents[currentIndex-1]['ko']) : '-';
            document.getElementById('next-text').innerText = currentIndex < contents.length - 1 ? (contents[currentIndex+1][inputLang] || contents[currentIndex+1]['ko']) : '-';
            
            // ?åÌä∏ ?ÖÎç∞?¥Ìä∏
            const hintDisplay = document.getElementById('hint-display');
            const hintLabel = document.getElementById('hint-lang-name');
            
            if (hintLang === 'none' || !currentData[hintLang]) {
                hintDisplay.style.visibility = 'hidden';
            } else {
                hintDisplay.innerText = currentData[hintLang];
                hintDisplay.style.visibility = 'visible';
            }

            inputField.value = '';
            inputField.classList.remove('error');
            speakText(targetTextContainer.innerText);
            
            // [v15] Ï≤?Í∏Ä?êÎ°ú ?∏Îìú Í∞Ä?¥Îìú ?¥Îèô
            setTimeout(() => {
                let firstChar = targetTextStr[0];
                if (firstChar) {
                    const dec = decomposeKo(firstChar);
                    if (dec.length > 0) firstChar = dec[0];
                }
                updateHandToChar(firstChar || 'Enter');
            }, 200);
        } else {
            finish();
        }
    }

    function getLangName(code) {
        const names = { 'ko': 'KOREAN', 'en': 'ENGLISH', 'ja': 'JAPANESE', 'zh': 'CHINESE' };
        return names[code] || 'HINT';
    }

    function toggleSound() {
        soundEnabled = !soundEnabled;
        localStorage.setItem('typingSound', soundEnabled ? 'on' : 'off');
        updateSoundIcon();
        if (soundEnabled) speakText(targetTextContainer.innerText);
    }

    function updateSoundIcon() {
        document.getElementById('sound-icon').innerText = soundEnabled ? '?îä' : '?îá';
        document.getElementById('sound-btn').classList.toggle('active', soundEnabled);
        document.getElementById('tts-speed-control').style.display = soundEnabled ? 'flex' : 'none';
    }

    function updateTTSRate(val) {
        ttsRates[inputLang] = val;
        localStorage.setItem('ttsRates', JSON.stringify(ttsRates));
        if (soundEnabled) speakText(targetTextContainer.innerText);
    }

    function speakText(text) {
        if (!soundEnabled || !text || text === 'Loading...' || text === '-') return;
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        
        const langMap = { 'ko': 'ko-KR', 'en': 'en-US', 'ja': 'ja-JP', 'zh': 'zh-CN' };
        const targetLang = langMap[inputLang] || 'ko-KR';
        msg.lang = targetLang;
        
        const voices = window.speechSynthesis.getVoices();
        const voice = voices.find(v => v.lang === targetLang) || voices.find(v => v.lang.startsWith(targetLang.split('-')[0]));
        if (voice) {
            msg.voice = voice;
        }
        
        msg.rate = parseFloat(ttsRates[inputLang] || '1.0');
        window.speechSynthesis.speak(msg);
    }

    function updateStatus() {
        document.getElementById('progress').innerText = `${currentIndex} / ${contents.length}`;
        const acc = totalChars === 0 ? 100 : Math.round(((totalChars - totalErrors) / totalChars) * 100);
        document.getElementById('accuracy').innerText = `${Math.max(0, acc)}%`;

        if (startTime) {
            const currentItemElapsed = itemStartTime ? (Date.now() - itemStartTime) : 0;
            const totalElapsedMin = (cumulativeTime + currentItemElapsed) / 60000;
            const wpm = Math.max(0, Math.round(completedStrokes / (totalElapsedMin || 0.001)));
            document.getElementById('wpm').innerText = wpm;

            if (itemStartTime) {
                const activeItemElapsed = Math.max(currentItemElapsed, 150);
                const curWpm = Math.round(getStrokeCount(inputField.value) / (activeItemElapsed / 60000));
                document.getElementById('cur-wpm').innerText = Math.min(curWpm, 1500); 
            }
        } else {
            document.getElementById('wpm').innerText = '0';
            document.getElementById('cur-wpm').innerText = '0';
        }
    }

    // ?Ä??Í∞êÏá† ?Ä?¥Î®∏ (?§ÏãúÍ∞??âÍ∑† ?Ä?òÎßå ?ÖÎç∞?¥Ìä∏)
    setInterval(() => {
        if (startTime && currentIndex < contents.length) {
            updateStatus();
        }
    }, 100);

    inputField.addEventListener('input', (e) => {
        if (!startTime) startTime = Date.now();
        if (!itemStartTime) itemStartTime = Date.now();
        
        const currentTarget = contents[currentIndex][inputLang] || contents[currentIndex]['ko'];
        const currentInput = inputField.value;
        
        let html = '';
        let isError = false;
        let nextCharToPress = ['Enter', 'Space'];

        for (let i = 0; i < currentTarget.length; i++) {
            if (i < currentInput.length) {
                if (currentTarget[i] === currentInput[i]) {
                    html += `<span style="color: #4ade80;">${currentTarget[i]}</span>`; // ?ºÏπò
                } else if (i === currentInput.length - 1) { // ?ÑÏû¨ Ï°∞Ìï© Ï§ëÏù∏ Í∏Ä??                    const targetDec = decomposeKo(currentTarget[i]);
                    const inputDec = decomposeKo(currentInput[i]);
                    let isPrefix = true;
                    let isSpillover = false;

                    for (let d = 0; d < Math.min(inputDec.length, targetDec.length); d++) {
                        if (inputDec[d] !== targetDec[d]) { isPrefix = false; break; }
                    }

                    if (isPrefix) {
                        if (inputDec.length <= targetDec.length) {
                            html += `<span style="color: #fbbf24;">${currentTarget[i]}</span>`; // Ï°∞Ìï© ÏßÑÌñâÏ§?(?∏Î????åÌä∏)
                            if (inputDec.length < targetDec.length) {
                                nextCharToPress = targetDec[inputDec.length];
                            } else {
                                nextCharToPress = ['Enter', 'Space'];
                            }
                        } else if (inputDec.length === targetDec.length + 1) {
                            if (i + 1 < currentTarget.length) {
                                const nextTargetDec = decomposeKo(currentTarget[i+1]);
                                if (nextTargetDec[0] === inputDec[inputDec.length - 1]) {
                                    isSpillover = true;
                                    html += `<span style="color: #fbbf24;">${currentTarget[i]}</span>`; 
                                    nextCharToPress = nextTargetDec[1] || ['Enter', 'Space']; 
                                } else {
                                    isPrefix = false; 
                                }
                            } else {
                                isPrefix = false; 
                            }
                        } else {
                            isPrefix = false;
                        }
                    }

                    if (!isPrefix && !isSpillover) {
                        html += `<span style="color: #f87171; background: rgba(248, 113, 113, 0.2); border-radius: 4px;">${currentTarget[i]}</span>`; // ?§Ì?
                        isError = true;
                        nextCharToPress = 'Backspace';
                    }
                } else { // Í≥ºÍ±∞???òÎ™ª Ïπ?Í∏Ä??                    html += `<span style="color: #f87171; background: rgba(248, 113, 113, 0.2); border-radius: 4px;">${currentTarget[i]}</span>`;
                    isError = true;
                    nextCharToPress = 'Backspace';
                }
            } else {
                html += `<span>${currentTarget[i]}</span>`; // ?ÑÏßÅ ??Ïπ?Í∏Ä??            }
        }

        if (!isError && (nextCharToPress === 'Enter' || (Array.isArray(nextCharToPress) && nextCharToPress.includes('Enter')))) {
            if (currentInput.length < currentTarget.length) {
                const targetDec = decomposeKo(currentTarget[currentInput.length]);
                nextCharToPress = targetDec[0];
            } else if (currentInput.length > currentTarget.length) {
                isError = true;
                nextCharToPress = 'Backspace';
            }
        } else if (isError) {
            nextCharToPress = 'Backspace';
        }

        if (targetTextContainer) targetTextContainer.innerHTML = html;
        updateHandToChar(nextCharToPress);

        if (isError) {
            inputField.classList.add('error');
        } else {
            inputField.classList.remove('error');
        }
        updateStatus();
    });

    inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            const currentTarget = contents[currentIndex][inputLang] || contents[currentIndex]['ko'];
            const currentInput = inputField.value.trim();

            if (currentInput === currentTarget) {
                if (e.key === ' ') e.preventDefault();
                
                // ?ÑÏû¨ Î¨∏Ìï≠ ?ÑÎ£å ?úÏ†ê???¥Îãπ Î¨∏Ìï≠ÎßåÏùò ?Ä?òÎ? ÏµúÍ≥† ?Ä?òÏ? ÎπÑÍµê
                if (itemStartTime) {
                    const itemElapsedMin = (Date.now() - itemStartTime) / 60000;
                    const itemStrokes = getStrokeCount(currentTarget);
                    const itemWpm = Math.round(itemStrokes / (itemElapsedMin || 0.001));
                    
                    // ÏµúÍ≥† ?Ä???ÖÎç∞?¥Ìä∏ (?ÑÏû¨ Î¨∏Ìï≠ ?Ä??Í∏∞Ï?)
                    if (itemWpm > maxWpm && itemWpm < 2000) {
                        maxWpm = itemWpm;
                        document.getElementById('max-wpm').innerText = maxWpm;
                    }

                    cumulativeTime += (Date.now() - itemStartTime);
                    itemStartTime = null;
                }

                completedStrokes += getStrokeCount(currentTarget);
                totalChars += currentTarget.length;

                currentIndex++;
                updateTarget();
                updateStatus();
            } else if (e.key === 'Enter') {
                inputField.classList.add('error');
                totalErrors++;
                updateStatus();
            }
        }
    });

    function retryPractice() {
        document.getElementById('result-modal').style.display = 'none';
        currentIndex = 0;
        completedStrokes = 0;
        totalErrors = 0;
        totalChars = 0;
        startTime = null;
        itemStartTime = null;
        cumulativeTime = 0;
        maxWpm = 0;
        inputField.value = '';
        inputField.disabled = false;
        document.getElementById('wpm').innerText = '0';
        document.getElementById('cur-wpm').innerText = '0';
        document.getElementById('max-wpm').innerText = '0';
        updateTarget();
        updateStatus();
        inputField.focus();
    }

    function finish() {
        const speed = parseInt(document.getElementById('wpm').innerText);
        const accuracy = parseFloat(document.getElementById('accuracy').innerText);
        const score = Math.round(speed * (accuracy / 100) * (contentType === 'word' ? 5 : 8));

        let unlockMsg = '';
        if (contentType === 'word' && speed >= 200) {
            const shortStorageKey = `typing_short_unlocked_${inputLang}`;
            if (localStorage.getItem(shortStorageKey) !== 'true') {
                localStorage.setItem(shortStorageKey, 'true');
                unlockMsg = "<br><span style='color:#fbbf24; font-size:16px;'>?îì ÏßßÏ?Í∏Ä ?∞Ïäµ Î™®ÎìúÍ∞Ä ?¥Ï†ú?òÏóà?µÎãà??</span>";
            }
        } else if (contentType === 'short' && speed >= 400) {
            const longStorageKey = `typing_long_unlocked_${inputLang}`;
            if (localStorage.getItem(longStorageKey) !== 'true') {
                localStorage.setItem(longStorageKey, 'true');
                unlockMsg = "<br><span style='color:#fbbf24; font-size:16px;'>?îì Í∏¥Í? ?∞Ïäµ Î™®ÎìúÍ∞Ä ?¥Ï†ú?òÏóà?µÎãà??</span>";
            }
        } else if (contentType === 'word' && speed < 200) {
            unlockMsg = "<br><span style='color:#f87171; font-size:14px;'>?âÍ∑† 200?Ä ?¥ÏÉÅ Í∏∞Î°ù ??ÏßßÏ?Í∏Ä ?∞Ïäµ???¥Î¶Ω?àÎã§.</span>";
        } else if (contentType === 'short' && speed < 400) {
            unlockMsg = "<br><span style='color:#f87171; font-size:14px;'>?âÍ∑† 400?Ä ?¥ÏÉÅ Í∏∞Î°ù ??Í∏¥Í? ?∞Ïäµ???¥Î¶Ω?àÎã§.</span>";
        }

        document.getElementById('final-score').innerHTML = score + (unlockMsg);
        document.getElementById('final-wpm').innerText = speed;
        document.getElementById('final-max').innerText = maxWpm;
        document.getElementById('final-accuracy').innerText = accuracy;
        document.getElementById('result-modal').style.display = 'flex';
    }

    function saveAndExit() {
        const speed = parseInt(document.getElementById('final-wpm').innerText);
        const accuracy = parseFloat(document.getElementById('final-accuracy').innerText);
        const score = parseInt(document.getElementById('final-score').innerText);

        fetch('{% url "save_score" %}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': 'x'
            },
            body: JSON.stringify({
                type: contentType,
                lang: inputLang,
                score: score,
                speed: speed,
                accuracy: accuracy
            })
        }).then(() => {
            location.href = `{% url "typing_home" %}?lang=${inputLang}`;
        });
    }



    init();

    window.addEventListener('resize', () => {
        if (showHands) setDefaultHandPositions();
    });


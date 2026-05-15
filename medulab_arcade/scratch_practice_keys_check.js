const isFullMember = false;
    const isPermanent = false;
    const showAds = true;
    
    const getStorage = () => isPermanent ? localStorage : sessionStorage;

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
        [
            {k:'Ctrl', c:'ControlLeft', w:'w-ctrl'}, {k:'Alt', c:'AltLeft'}, {k:'Space', c:'Space', w:'w-space'}, {k:'Alt', c:'AltRight'}, {k:'Ctrl', c:'ControlRight', w:'w-ctrl'}
        ]
    ];

    const FINGER_MAP = {
        'L5': ['`', '1', 'Q', 'A', 'Z', 'Tab', 'CapsLock', 'ShiftLeft', 'ControlLeft', '??, '??, '??],
        'L4': ['2', 'W', 'S', 'X', '??, '??, '??],
        'L3': ['3', 'E', 'D', 'C', '??, '??, '??],
        'L2': ['4', '5', 'R', 'T', 'F', 'G', 'V', 'B', '??, '??, '??, '??, '??, '??],
        'L1': ['Space'],
        'R1': ['Space'],
        'R2': ['6', '7', 'Y', 'U', 'H', 'J', 'N', 'M', '??, '??, '??, '??, '??, '??],
        'R3': ['8', 'I', 'K', ',', '??, '??],
        'R4': ['9', 'O', 'L', '.', '??, '??],
        'R5': ['0', '-', '=', 'P', '[', ']', '\\', ';', '\'', '/', 'Enter', 'ShiftRight', '??]
    };

    const LEVELS = {
        'ko': {
            'home': ['??, '??, '??, '??, '??, '??, '??, '??, '??, ';', "'"],
            'top': ['??, '??, '??, '??, '??, '??, '??, '??, '??, '??, '[', ']'],
            'bottom': ['??, '??, '??, '??, '??, '??, '??, ',', '.', '/'],
            'number': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
            'shift': ['??, '??, '??, '??, '??, '??, '??, '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '~', '{', '}', ':', '"', '<', '>', '?']
        },
        'en': {
            'home': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'"],
            'top': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']'],
            'bottom': ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/'],
            'number': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
            'shift': ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '~', '{', '}', ':', '"', '<', '>', '?']
        },
        'ja': {
            'home': ['??, '??, '??, '??, '??, '??, '??, '??, '??, '??],
            'top': ['??, '??, '??, '??, '??, '??, '??, '??, '??, '??],
            'bottom': ['??, '??, '??, '??, '??, '??, '??, '??, '??, '??],
            'number': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
            'shift': ['??, '??, '??, '??, '??, '??, '??, '??, '??]
        },
        'zh': {
            'home': ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            'top': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            'bottom': ['Z', 'X', 'C', 'V', 'B', 'N', 'M'],
            'number': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
            'shift': ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+']
        }
    };
    Object.keys(LEVELS).forEach(l => {
        LEVELS[l].all = [].concat(...Object.values(LEVELS[l]));
    });

    const EN_TO_KO = {'q':'??,'w':'??,'e':'??,'r':'??,'t':'??,'y':'??,'u':'??,'i':'??,'o':'??,'p':'??,'a':'??,'s':'??,'d':'??,'f':'??,'g':'??,'h':'??,'j':'??,'k':'??,'l':'??,'z':'??,'x':'??,'c':'??,'v':'??,'b':'??,'n':'??,'m':'??,'Q':'??,'W':'??,'E':'??,'R':'??,'T':'??,'O':'??,'P':'??};
    const EN_TO_JA = {'a':'??,'i':'??,'u':'??,'e':'??,'o':'??,'k':'??,'s':'??,'t':'??,'n':'??,'h':'??,'m':'??,'y':'??,'r':'??,'w':'??};

    const progressPrefix = 'typing_guest';
    const progressKey = (name) => `${progressPrefix}_${name}`;
    let currentLang = "ko";
    let currentLevel = "home";
    let storageKey = progressKey(`typing_unlocked_levels_${currentLang}`);
    let wordUnlockKey = progressKey(`typing_word_unlocked_${currentLang}`);

    const PROGRESSION = ['home', 'top', 'bottom', 'number', 'shift', 'all'];
    let unlockedLevels = JSON.parse(getStorage().getItem(storageKey) || '["home"]');

    function updateLockStates() {
        document.querySelectorAll('.level-btn').forEach(btn => {
            const level = btn.getAttribute('data-level');
            if (unlockedLevels.includes(level)) {
                btn.classList.remove('locked');
            } else {
                btn.classList.add('locked');
            }
        });
    }

    function unlockNextLevel(current) {
        const idx = PROGRESSION.indexOf(current);
        if (idx !== -1 && idx < PROGRESSION.length - 1) {
            const next = PROGRESSION[idx + 1];
            if (!unlockedLevels.includes(next)) {
                unlockedLevels.push(next);
                getStorage().setItem(storageKey, JSON.stringify(unlockedLevels));
                updateLockStates();
                return next;
            }
            return 'already_unlocked';
        } else if (current === 'all') {
            getStorage().setItem(wordUnlockKey, 'true');
            return 'word_practice_ready';
        }
        return null;
    }

    let targetChar = '', prevChar = '-', nextCharBuffer = [];
    let completedCount = 0, completedStrokes = 0, errors = 0, totalCount = 50;
    let timeLeft = 60, startTime = null, timerInterval = null, itemStartTime = null, cumulativeTime = 0, maxWpm = 0;
    let soundEnabled = getStorage().getItem('typingSound') === 'on';
    let showHands = getStorage().getItem('showHands') !== 'off';

    function initKeyboard() {
        const kb = document.getElementById('v-keyboard');
        kb.innerHTML = '';
        
        const activeLevelChars = LEVELS[currentLang] ? LEVELS[currentLang][currentLevel] : [];
        const isAllMode = currentLevel === 'all';

        KEYBOARD_LAYOUT_DATA.forEach((row, idx) => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'key-row';
            
            if (idx === 1) rowDiv.style.marginLeft = '15px'; // ?꾩떎?곸씤 ?먰뙋 諛곗뿴???꾪븳 誘몄꽭 議곗젙
            if (idx === 2) rowDiv.style.marginLeft = '35px';
            if (idx === 3) rowDiv.style.marginLeft = '60px';
            
            row.forEach(item => {
                const keyDiv = document.createElement('div');
                keyDiv.className = `key ${item.w || ''}`;
                
                let keyId = item.c || item.k;
                if (currentLang === 'ko' && item.ko) keyId = item.ko;
                keyDiv.id = `key-${keyId}`;
                
                let charInLevel = false;
                if (!isAllMode) {
                    charInLevel = (item.ko && activeLevelChars.includes(item.ko)) || 
                                  activeLevelChars.includes(item.k) ||
                                  (currentLang === 'ko' && item.koS && activeLevelChars.includes(item.koS)) ||
                                  (item.s && activeLevelChars.includes(item.s));
                                  
                    const isFunctionalKey = item.w || ['Shift', 'Backspace', 'Enter', 'Alt', 'Ctrl', 'Tab', 'Caps'].includes(item.k);
                    
                    if (charInLevel) {
                        keyDiv.classList.add('zone-active');
                    } else if (!isFunctionalKey) {
                        keyDiv.classList.add('zone-inactive');
                    }
                }
                
                let shiftCharHTML = '';
                let shiftChar = item.s || '';
                if (currentLang === 'ko' && item.koS) shiftChar = item.koS;
                
                if (shiftChar) {
                    const shiftLabelColor = (charInLevel && activeLevelChars.includes(shiftChar)) ? '#f43f5e' : '#94a3b8';
                    shiftCharHTML = `<span style="font-size:10.5px; color:${shiftLabelColor}; position:absolute; top:4px; right:6px; font-weight:800;">${shiftChar}</span>`;
                }

                if (currentLang === 'ko' && item.ko) {
                    const subLabelColor = (charInLevel && activeLevelChars.includes(item.ko)) ? '#8b5cf6' : '#64748b';
                    keyDiv.innerHTML = `<span style="font-size:10.5px; color:${subLabelColor}; position:absolute; top:4px; left:6px; font-weight:800;">${item.k}</span>${shiftCharHTML}<span style="font-weight:900; margin-top:8px;">${item.ko}</span>`;
                } else if (item.k.length === 1) { // Numbers and letters
                    keyDiv.innerHTML = `${shiftCharHTML}<span style="font-weight:900; margin-top:${shiftChar ? '8px' : '0'};">${item.k}</span>`;
                } else {
                    keyDiv.innerText = item.k;
                }
                rowDiv.appendChild(keyDiv);
            });
            kb.appendChild(rowDiv);
        });
        resetPractice();
        nextChar();
        updateSoundIcon();
        requestAnimationFrame(setDefaultHandPositions);
    }

    function setLang(lang) {
        currentLang = lang;
        // ?몄뼱 蹂寃????ㅽ넗由ъ? ??諛??곹깭 ?щ룞湲고솕 (v15 媛쒖꽑)
        storageKey = progressKey(`typing_unlocked_levels_${currentLang}`);
        wordUnlockKey = progressKey(`typing_word_unlocked_${currentLang}`);
        unlockedLevels = JSON.parse(getStorage().getItem(storageKey) || '["home"]');

        document.querySelectorAll('.lang-toggle .toggle-btn').forEach(btn => {
            if (btn.id === 'sound-btn') return;
            const onclick = btn.getAttribute('onclick') || '';
            btn.classList.toggle('active', onclick.includes(`'${lang}'`));
        });
        
        updateLockStates();
        initKeyboard();
    }

    function setLevel(level) {
        if (!unlockedLevels.includes(level)) {
            alert(`?뵏 [${getLangName(currentLang)}] ?댁쟾 ?④퀎瑜??뺥솗??80% ?댁긽?쇰줈 ?듦낵?댁빞 ?대┰?덈떎!`);
            return;
        }
        currentLevel = level;
        document.querySelectorAll('.level-btn').forEach(btn => {
            const levelAttr = btn.getAttribute('data-level');
            btn.classList.toggle('active', levelAttr === level);
        });
        resetPractice();
        initKeyboard(); // [v16] ?④퀎 ?꾪솚 ???ㅻ낫??援ъ뿭 ?ъ깮???곕룞
        nextChar();
    }

    function resetPractice() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        
        // ?꾩옱 ?덈꺼???좉꺼?덈뒗吏 ?ㅼ떆 ??踰?泥댄겕 (URL 吏곸젒 ?묎렐 ???鍮?
        if (!unlockedLevels.includes(currentLevel)) {
            currentLevel = 'home';
            getStorage().setItem(storageKey, JSON.stringify(unlockedLevels));
            alert("?뵏 ?꾩쭅 ?대━吏 ?딆? ?④퀎?낅땲?? 湲곕낯?먮━遺???쒖옉?섏꽭??");
            updateLockStates();
        }

        completedCount = 0; completedStrokes = 0; errors = 0; startTime = null; itemStartTime = null; cumulativeTime = 0; maxWpm = 0; timeLeft = 60;
        targetChar = ''; prevChar = '-'; nextCharBuffer = [];
        
        const timeBar = document.getElementById('time-bar');
        if (timeBar) {
            timeBar.style.width = '100%';
            timeBar.classList.remove('danger');
        }
        const timeText = document.getElementById('time-text');
        if (timeText) {
            timeText.innerText = '60s';
            timeText.style.color = '#4ade80';
        }
        updateStatus();
    }

    function updateStatus() {
        const progressEl = document.getElementById('progress');
        if (progressEl) progressEl.innerText = `${completedCount}/${totalCount}`;
    }

    const SHIFT_MAP = {
        '??:'??,'??:'??,'??:'??,'??:'??,'??:'??,'??:'??,'??:'??,
        'Q':'??,'W':'??,'E':'??,'R':'??,'T':'??,'O':'??,'P':'??,
        '!':'1','@':'2','#':'3','$':'4','%':'5','^':'6','&':'7','*':'8','(':'9',')':'0','_':'-','+':'=',
        '~':'`','{':'[','}':']','|':'\\',':':';','"':'\'','<':',','>':'.','?':'/',
        ' ': 'Space'
    };

    // 臾몄옄 ???ㅻ낫??DOM ID 肄붾뱶 留ㅽ븨 (?レ옄/?뱀닔??泥섎━)
    const CHAR_TO_CODE = {
        '`':'Backquote','1':'Digit1','2':'Digit2','3':'Digit3','4':'Digit4',
        '5':'Digit5','6':'Digit6','7':'Digit7','8':'Digit8','9':'Digit9','0':'Digit0',
        '-':'Minus','=':'Equal','[':'BracketLeft',']':'BracketRight','\\':'Backslash',
        ';':'Semicolon',"'":'Quote',',':'Comma','.':'Period','/':'Slash',
        'Space':'Space','Enter':'Enter','Tab':'Tab'
    };

    function getKeyEl(char) {
        if (CHAR_TO_CODE[char]) return document.getElementById(`key-${CHAR_TO_CODE[char]}`);
        let el = document.getElementById(`key-${char}`);
        if (el) return el;
        if (char.length === 1 && /[a-zA-Z]/.test(char))
            return document.getElementById(`key-Key${char.toUpperCase()}`);
        return document.getElementById(`key-${char.toUpperCase()}`);
    }

    function positionHand(handEl, fingerId, keyEl, wrapRect, stateClass) {
        const tipEl = document.getElementById(`tip-${fingerId}`);
        if (!tipEl || !keyEl || !wrapRect) return;
        const keyRect = keyEl.getBoundingClientRect();
        const keyTop  = keyRect.top  - wrapRect.top  + keyRect.height / 2;
        const keyLeft = keyRect.left - wrapRect.left + keyRect.width  / 2;
        const tipX = tipEl.cx.baseVal.value;
        const tipY = tipEl.cy.baseVal.value;
        const scale = 460 / 200;   // CSS width? 諛섎뱶???쇱튂
        handEl.style.top  = `${keyTop  - tipY * scale - 15}px`;
        handEl.style.left = `${keyLeft - tipX * scale}px`;
        handEl.style.transform = 'none';
        handEl.classList.remove('active', 'rest', 'home');
        if (stateClass) handEl.classList.add(stateClass);
    }

    // ?묒넀?????ъ??섏뿉 怨좎젙 (?쇱넀: ??F, ?ㅻⅨ?? ??J)
    function setDefaultHandPositions() {
        const wrap = document.querySelector('.keyboard-wrapper');
        if (!wrap) return;
        const wrapRect = wrap.getBoundingClientRect();
        const leftHomeEl  = currentLang === 'ko' ? document.getElementById('key-??) : document.getElementById('key-KeyF');
        const rightHomeEl = currentLang === 'ko' ? document.getElementById('key-??) : document.getElementById('key-KeyJ');
        positionHand(document.getElementById('hand-left'),  'L2', leftHomeEl,  wrapRect, 'home');
        positionHand(document.getElementById('hand-right'), 'R2', rightHomeEl, wrapRect, 'home');
    }

    function getRandomChar(excludeChar, possibleChars) {
        if (possibleChars.length <= 1) return possibleChars[0];
        let rand;
        do {
            rand = possibleChars[Math.floor(Math.random() * possibleChars.length)];
        } while (rand === excludeChar);
        return rand;
    }

    function nextChar() {
        let possibleChars = [];
        if (currentLevel === 'all') { // ?꾩껜?먮━ 紐⑤뱶????            Object.values(LEVELS[currentLang]).forEach(arr => possibleChars = possibleChars.concat(arr));
        } else {
            possibleChars = LEVELS[currentLang][currentLevel];
        }
        
        if (!targetChar) {
            targetChar = possibleChars[Math.floor(Math.random() * possibleChars.length)];
            nextCharBuffer = [getRandomChar(targetChar, possibleChars)];
        } else {
            prevChar = targetChar;
            targetChar = nextCharBuffer[0];
            nextCharBuffer = [getRandomChar(targetChar, possibleChars)];
        }
        
        document.getElementById('prev-char').innerText = prevChar;
        document.getElementById('target-char').innerText = targetChar;
        document.getElementById('next-char').innerText = nextCharBuffer[0];
        
        document.querySelectorAll('.key').forEach(k => {
            k.classList.remove('target');
            if (k.dataset.origText) {
                const innerSpan = k.querySelector('span:nth-child(2)') || k;
                if(innerSpan.tagName === 'SPAN') {
                    innerSpan.innerText = k.dataset.origText;
                } else {
                    k.innerText = k.dataset.origText;
                }
                delete k.dataset.origText;
            }
        });
        document.querySelectorAll('.finger-group').forEach(f => f.classList.remove('striking'));
        const handLeft  = document.getElementById('hand-left');
        const handRight = document.getElementById('hand-right');

        let lookupChar = targetChar;
        let isShiftRequired = false;
        if (SHIFT_MAP[targetChar]) {
            lookupChar = SHIFT_MAP[targetChar];
            isShiftRequired = (targetChar !== ' ' && targetChar !== lookupChar);
        }

        const targetDiv = getKeyEl(lookupChar);
        if (targetDiv) {
            targetDiv.classList.add('target');
            
            if (isShiftRequired) {
                const innerSpan = targetDiv.querySelector('span:nth-child(2)') || targetDiv;
                if (!targetDiv.dataset.origText) {
                    targetDiv.dataset.origText = innerSpan.innerText;
                }
                innerSpan.innerText = targetChar;
            }
            let targetFinger = '';
            for (const [fingerId, keys] of Object.entries(FINGER_MAP)) {
                if (keys.includes(lookupChar) || keys.includes(lookupChar.toUpperCase())) {
                    targetFinger = fingerId; break;
                }
            }

            if (targetFinger) {
                const isLeftMain  = targetFinger.startsWith('L');
                const mainHand    = isLeftMain ? handLeft  : handRight;
                const otherHand   = isLeftMain ? handRight : handLeft;
                const wrap        = document.querySelector('.keyboard-wrapper');
                const wrapRect    = wrap.getBoundingClientRect();

                // 硫붿씤 ?? ?대떦 ?먭??쎌씠 ???꾩뿉 ?ㅻ룄濡??대룞
                document.getElementById(`finger-${targetFinger}`)?.classList.add('striking');
                positionHand(mainHand, targetFinger, targetDiv, wrapRect, 'active');

                if (isShiftRequired) {
                    // ?ы봽?? 諛섎? ???덈겮?먭??쎈룄 ?대룞
                    const shiftKeyId  = isLeftMain ? 'ShiftRight' : 'ShiftLeft';
                    const shiftDiv    = document.getElementById(`key-${shiftKeyId}`);
                    const shiftFinger = isLeftMain ? 'R5' : 'L5';
                    if (shiftDiv) {
                        shiftDiv.classList.add('target');
                        document.getElementById(`finger-${shiftFinger}`)?.classList.add('striking');
                        positionHand(otherHand, shiftFinger, shiftDiv, wrapRect, 'active');
                    }
                } else {
                    const homeFinger = isLeftMain ? 'R2' : 'L2';
                    const homeEl = isLeftMain
                        ? (currentLang === 'ko' ? document.getElementById('key-??) : document.getElementById('key-KeyJ'))
                        : (currentLang === 'ko' ? document.getElementById('key-??) : document.getElementById('key-KeyF'));
                    positionHand(otherHand, homeFinger, homeEl, wrapRect, 'home');
                }
            }
        }
        speakText(targetChar);
    }

    function startTimer() {
        if (timerInterval) return;
        timerInterval = setInterval(() => {
            timeLeft--;
            const timeBar = document.getElementById('time-bar');
            const timeText = document.getElementById('time-text');
            
            if (timeBar) {
                const percent = (timeLeft / 60) * 100;
                timeBar.style.width = `${percent}%`;
                if (timeLeft <= 10) timeBar.classList.add('danger');
            }
            if (timeText) {
                timeText.innerText = `${timeLeft}s`;
                if (timeLeft <= 10) timeText.style.color = '#f87171';
            }
            
            if (timeLeft <= 0) { clearInterval(timerInterval); finishPractice(false); }
        }, 1000);
    }

    window.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.altKey || e.metaKey || e.key === 'Shift') return;
        if (timeLeft <= 0 || completedCount >= totalCount) return;

        if (!startTime) { startTime = Date.now(); startTimer(); }
        if (!itemStartTime) itemStartTime = Date.now();

        let inputChar = e.key;
        if (currentLang === 'ko') inputChar = EN_TO_KO[e.key] || e.key;
        else if (currentLang === 'ja') inputChar = EN_TO_JA[e.key] || e.key;
        else if (currentLang === 'zh' || currentLang === 'en') {
            if (inputChar.length === 1 && targetChar === targetChar.toUpperCase()) inputChar = inputChar.toUpperCase();
        }

        const keyDiv = document.getElementById(`key-${e.code}`) || getKeyEl(inputChar);
        if (keyDiv) {
            keyDiv.classList.add('active');
            setTimeout(() => keyDiv.classList.remove('active'), 100);
        }

        if (inputChar === targetChar || (currentLang === 'ja' && EN_TO_JA[e.key] === targetChar)) {
            completedStrokes += 1;
            completedCount++;
            cumulativeTime += (Date.now() - itemStartTime);
            itemStartTime = null;
            if (completedCount >= totalCount) { if (timerInterval) clearInterval(timerInterval); finishPractice(true); }
            else nextChar();
        } else {
            if (inputChar.length === 1) errors++;
        }
        updateStatus();
    });

    function finishPractice(isSuccess) {
        document.getElementById('final-status').innerText = isSuccess ? "MISSION COMPLETE!" : "TIME OUT!";
        document.getElementById('final-status').style.color = isSuccess ? "#4ade80" : "#f87171";
        
        // ?대? 蹂??湲곕컲 ?곗씠???곗텧
        const accuracy = (completedCount + errors === 0) ? 100 : Math.round((completedCount / (completedCount + errors)) * 100);
        const totalElapsedMin = cumulativeTime / 60000;
        const wpm = Math.round(completedStrokes / (totalElapsedMin || 0.001));

        let unlockMsg = '';
        if (isSuccess && accuracy >= 80) {
            const unlocked = unlockNextLevel(currentLevel);
            if (unlocked) {
                if (unlocked === 'word_practice') unlockMsg = "<br><span style='color:#fbbf24; font-size:16px;'>?뵑 ?⑥뼱 ?곗뒿 紐⑤뱶媛 ?댁젣?섏뿀?듬땲??</span>";
                else unlockMsg = "<br><span style='color:#fbbf24; font-size:16px;'>?뵑 ?덈줈???④퀎媛 ?대졇?듬땲??</span>";
            }
        } else if (isSuccess && accuracy < 80) {
            unlockMsg = "<br><span style='color:#f87171; font-size:14px;'>?뺥솗??80% ?댁긽?댁뼱???ㅼ쓬 ?④퀎媛 ?대┰?덈떎.</span>";
        }

        document.getElementById('final-accuracy').innerText = accuracy;
        document.getElementById('final-time').innerText = timeLeft;
        const finalMessage = document.getElementById('final-message');
        finalMessage.innerHTML = unlockMsg;
        document.getElementById('result-modal').style.display = 'flex';
    }

    function retryPractice() { document.getElementById('result-modal').style.display = 'none'; resetPractice(); nextChar(); }
    /*
    
    // [v16] ?먭???媛?대뱶 ?좉? ?쒖뒪??    */
    /*
    function toggleHands() {
        showHands = !showHands;
        getStorage().setItem('showHands', showHands ? 'on' : 'off');
        applyHandToggle();
    }

    */
    function toggleHands() {
        showHands = !showHands;
        getStorage().setItem('showHands', showHands ? 'on' : 'off');
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

    function saveAndExit() {
        // ?대? 蹂??湲곕컲 理쒖쥌 ?곗씠???곗텧
        const accuracy = (completedCount + errors === 0) ? 100 : Math.round((completedCount / (completedCount + errors)) * 100);
        const totalElapsedMin = cumulativeTime / 60000;
        const wpm = Math.round(completedStrokes / (totalElapsedMin || 0.001));

        fetch('/save/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': 'token'},
            body: JSON.stringify({type: 'key', lang: currentLang, score: wpm * 10, speed: wpm, accuracy: accuracy})
        }).then(() => { location.href = `/practice/keys/?lang=${currentLang}`; });
    }

    function toggleSound() { soundEnabled = !soundEnabled; getStorage().setItem('typingSound', soundEnabled ? 'on' : 'off'); updateSoundIcon(); }
    function updateSoundIcon() { document.getElementById('sound-icon').innerText = soundEnabled ? '?뵄' : '?뵁'; }
    function speakText(text) {
        if (!soundEnabled || !text || text === '-') return;
        window.speechSynthesis.cancel();
        
        let spokenText = text;
        if (currentLang === 'ko') {
            const koMap = {
                ';': '?몃?肄쒕줎', "'": '?묒??곗샂??, ',': '?쇳몴', '.': '留덉묠??, '/': '?щ옒??, 
                '[': '?愿꾪샇 ?닿린', ']': '?愿꾪샇 ?リ린',
                ')': '愿꾪샇?リ린', '(': '愿꾪샇?닿린', '!': '?먮굦??, '?': '臾쇱쓬??, ':': '肄쒕줎', 
                '$': '?щ윭', '{': '以묎큵?몄뿴湲?, '}': '以묎큵?몃떕湲?, '%': '?쇱꽱??, '<': '?묐떎', 
                '>': '?щ떎', '+': '?뚮윭??, '~': '臾쇨껐', '*': '蹂?, '^': '罹먮┸',
                '"': '?곕뵲?댄몴', '#': '??, '_': '?몃뜑?쇱씤'
            };
            if (koMap[text]) spokenText = koMap[text];
        } else {
            const enMap = {
                ';': 'semicolon', "'": 'quote', ',': 'comma', '.': 'period', '/': 'slash', 
                '[': 'left bracket', ']': 'right bracket',
                ')': 'right parenthesis', '(': 'left parenthesis', '!': 'exclamation', '?': 'question mark', ':': 'colon', 
                '$': 'dollar', '{': 'left brace', '}': 'right brace', '%': 'percent', '<': 'less than', 
                '>': 'greater than', '+': 'plus', '~': 'tilde', '*': 'asterisk', '^': 'caret',
                '"': 'double quote', '#': 'hash', '_': 'underline'
            };
            if (enMap[text]) spokenText = enMap[text];
        }

        const msg = new SpeechSynthesisUtterance(spokenText);
        msg.lang = (currentLang === 'ko') ? 'ko-KR' : (currentLang === 'ja' ? 'ja-JP' : 'en-US');
        msg.rate = 1.3;
        window.speechSynthesis.speak(msg);
    }

    updateLockStates();
    
    // UI 踰꾪듉 ?곹깭 ?숆린??(珥덇린 ?뚮뜑留???parameter ??留욎떠 ?좏깮 踰꾪듉 ?낅뜲?댄듃)
    document.querySelectorAll('.lang-toggle .toggle-btn:not(.tp-control-btn)').forEach(btn => {
        const onclick = btn.getAttribute('onclick') || '';
        btn.classList.toggle('active', onclick.includes(`'${currentLang}'`));
    });
    document.querySelectorAll('.level-btn').forEach(btn => {
        const levelAttr = btn.getAttribute('data-level');
        btn.classList.toggle('active', levelAttr === currentLevel);
    });
    
    // init ?섑띁: 愿묎퀬 ?몄텧 ?щ????곕씪 ?쒖옉
    function startWithAd() {
        if (!showAds) {
            initKeyboard();
            return;
        }

        const overlay = document.getElementById('ad-overlay');
        const timerText = document.getElementById('ad-timer');
        overlay.style.display = 'flex';
        let count = 3;

        const interval = setInterval(() => {
            count--;
            timerText.innerText = count;
            if (count <= 0) {
                clearInterval(interval);
                overlay.style.display = 'none';
                initKeyboard();
            }
        }, 1000);
    }

    startWithAd();

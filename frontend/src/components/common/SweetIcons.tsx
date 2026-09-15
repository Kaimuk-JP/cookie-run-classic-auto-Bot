import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

/**
 * Official CookieRun Hero Warrior Icon (คุกกี้ผู้กล้าหาญชุดนักรบดาบคู่)
 * Enhanced & polished vector representation of the iconic CookieRun game icon:
 * - Dynamic fiery speedline background with glowing sparks
 * - Determined warrior running pose with dual swords & skull buttons
 * - Traditional Gat / swashbuckler warrior hat with white icing beads & lime spiral crest
 * - Fierce lightning icing eyebrows, laughing warrior grin, and bright cyan eyes
 */
export const CookieWarriorHeroIcon: React.FC<IconProps> = ({ className = 'w-10 h-10', size = 50 }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 500 500"
      width={size}
      height={size}
      className={className}
    >
      <defs>
        {/* Dynamic fiery radial background */}
        <radialGradient id="warriorBg" cx="20%" cy="20%" r="90%">
          <stop offset="0%" stopColor="#ff4500" />
          <stop offset="55%" stopColor="#b80c00" />
          <stop offset="100%" stopColor="#550000" />
        </radialGradient>

        {/* Soft drop shadow */}
        <filter id="warriorShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="3" dy="5" stdDeviation="4" floodColor="#2a0000" floodOpacity="0.45" />
        </filter>

        {/* Ember Glow */}
        <radialGradient id="sparkGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFF9D2" />
          <stop offset="50%" stopColor="#FFE066" />
          <stop offset="100%" stopColor="#FF9900" stopOpacity="0" />
        </radialGradient>

        <style>{`
          @keyframes crRunnerBob {
            0% { transform: translateY(0px) rotate(0deg) scale(1, 1); }
            50% { transform: translateY(-9px) rotate(-2.5deg) scale(0.97, 1.03); }
            100% { transform: translateY(4px) rotate(2deg) scale(1.02, 0.98); }
          }
          @keyframes crLegBack {
            0% { transform: rotate(-28deg); }
            50% { transform: rotate(14deg); }
            100% { transform: rotate(-32deg); }
          }
          @keyframes crArmBack {
            0% { transform: rotate(30deg); }
            50% { transform: rotate(-24deg); }
            100% { transform: rotate(34deg); }
          }
          @keyframes crSwordArm {
            0% { transform: rotate(-16deg) translateY(-6px); }
            50% { transform: rotate(18deg) translateY(8px); }
            100% { transform: rotate(-18deg) translateY(-4px); }
          }
          @keyframes crHeadBob {
            0% { transform: rotate(0deg) translateY(0px); }
            50% { transform: rotate(-3deg) translateY(-4px); }
            100% { transform: rotate(3deg) translateY(3px); }
          }
          @keyframes crSpeedLines {
            0% { transform: translateX(25px) translateY(-12px); opacity: 0.2; }
            50% { opacity: 0.6; }
            100% { transform: translateX(-35px) translateY(16px); opacity: 0.2; }
          }
          @keyframes crSparkFlicker {
            0%, 100% { transform: scale(0.85); opacity: 0.5; }
            50% { transform: scale(1.35); opacity: 1; }
          }
          .cr-runner {
            transform-origin: 250px 380px;
            animation: crRunnerBob 0.36s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate;
          }
          .cr-leg-back {
            transform-origin: 110px 420px;
            animation: crLegBack 0.36s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate;
          }
          .cr-arm-back {
            transform-origin: 140px 240px;
            animation: crArmBack 0.36s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate;
          }
          .cr-sword-arm {
            transform-origin: 320px 330px;
            animation: crSwordArm 0.36s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate;
          }
          .cr-head {
            transform-origin: 285px 280px;
            animation: crHeadBob 0.36s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite alternate;
          }
          .cr-speedlines {
            animation: crSpeedLines 0.45s linear infinite;
          }
          .cr-spark {
            transform-box: fill-box;
            transform-origin: center;
            animation: crSparkFlicker 0.6s ease-in-out infinite alternate;
          }
        `}</style>
      </defs>

      {/* Background Rounded Card */}
      <rect width="500" height="500" rx="60" fill="url(#warriorBg)" />

      {/* Dynamic Speed Stripes */}
      <g className="cr-speedlines">
        <path d="M-80 180 L580 -80 L620 -30 L-40 230 Z" fill="#ff5300" opacity="0.3" />
        <path d="M-80 340 L580 80 L620 130 L-40 390 Z" fill="#ff5300" opacity="0.3" />
        <path d="M-50 510 L600 240 L640 290 L-10 560 Z" fill="#ff5300" opacity="0.3" />
      </g>

      {/* Floating Fiery Ember Particles */}
      <g className="cr-spark">
        <circle cx="28" cy="360" r="6" fill="#ffe066" opacity="0.85" />
        <circle cx="28" cy="360" r="12" fill="url(#sparkGlow)" opacity="0.5" />
        <circle cx="475" cy="460" r="8" fill="#ffe066" opacity="0.9" />
        <circle cx="475" cy="460" r="16" fill="url(#sparkGlow)" opacity="0.5" />
        <circle cx="470" cy="300" r="9" fill="#ffe066" opacity="0.85" />
        <circle cx="470" cy="300" r="18" fill="url(#sparkGlow)" opacity="0.5" />
        <circle cx="60" cy="110" r="4" fill="#ffe066" opacity="0.75" />
        <circle cx="430" cy="70" r="5" fill="#ffe066" opacity="0.8" />
        <circle cx="360" cy="460" r="6" fill="#ffe066" opacity="0.85" />
      </g>

      {/* Entire Animated Runner Character */}
      <g id="cookie-runner" className="cr-runner" filter="url(#warriorShadow)">
        {/* Back Running Foot / Leg (Animated Pumping) */}
        <g className="cr-leg-back">
          <path
            d="M100 400 C80 415 70 440 85 460 C105 475 130 460 135 435 Z"
            fill="#c98042"
            stroke="#2a1102"
            strokeWidth="6.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>

        {/* Back Arm (Left) (Animated Swinging) */}
        <g className="cr-arm-back">
          <path
            d="M140 210 C80 210 40 235 40 270 C40 295 70 305 105 285 L145 245 Z"
            fill="#c98042"
            stroke="#2a1102"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>

        {/* Main Body & Front Stride Leg */}
        <path
          d="M140 240 C140 240 95 360 120 445 C130 475 165 480 190 435 C210 400 275 410 325 440 C370 460 410 400 365 370 C315 335 315 270 305 225 Z"
          fill="#c98042"
          stroke="#2a1102"
          strokeWidth="7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Golden Speed Aura Contour along the Back */}
        <path
          d="M370 375 C395 395 370 440 335 430 C295 415 225 395 195 430"
          fill="none"
          stroke="#f6ea9b"
          strokeWidth="6"
          strokeLinecap="round"
        />

        {/* 2 White Icing Skull Buttons on Chest */}
        <g transform="translate(218, 355)">
          <path
            d="M12 0 C5 0 0 6 0 13 C0 18 3 22 7 24 L7 28 C7 29.5 8.5 30 10 30 L22 30 C23.5 30 25 29.5 25 28 L25 24 C29 22 32 18 32 13 C32 6 27 0 20 0 Z"
            fill="#ffffff"
            stroke="#2a1102"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />
          <circle cx="9" cy="14" r="3" fill="#2a1102" />
          <circle cx="21" cy="14" r="3" fill="#2a1102" />
          <line x1="12" y1="24" x2="12" y2="29" stroke="#2a1102" strokeWidth="2" />
          <line x1="16" y1="24" x2="16" y2="29" stroke="#2a1102" strokeWidth="2" />
          <line x1="20" y1="24" x2="20" y2="29" stroke="#2a1102" strokeWidth="2" />
        </g>
        <g transform="translate(202, 408) scale(0.88)">
          <path
            d="M12 0 C5 0 0 6 0 13 C0 18 3 22 7 24 L7 28 C7 29.5 8.5 30 10 30 L22 30 C23.5 30 25 29.5 25 28 L25 24 C29 22 32 18 32 13 C32 6 27 0 20 0 Z"
            fill="#ffffff"
            stroke="#2a1102"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />
          <circle cx="9" cy="14" r="3" fill="#2a1102" />
          <circle cx="21" cy="14" r="3" fill="#2a1102" />
          <line x1="12" y1="24" x2="12" y2="29" stroke="#2a1102" strokeWidth="2" />
          <line x1="16" y1="24" x2="16" y2="29" stroke="#2a1102" strokeWidth="2" />
          <line x1="20" y1="24" x2="20" y2="29" stroke="#2a1102" strokeWidth="2" />
        </g>

        {/* Diagonal Sword & Scabbard across Torso */}
        <path d="M85 280 Q215 390 275 470" fill="none" stroke="#2a1102" strokeWidth="20" strokeLinecap="round" />
        <path d="M85 280 Q215 390 275 470" fill="none" stroke="#ffffff" strokeWidth="14" strokeLinecap="round" />
        <path d="M100 290 L125 325 L145 305 Z" fill="#0f4825" />
        <path d="M135 328 L160 363 L180 343 Z" fill="#b91c1c" />
        <path d="M170 368 L195 403 L215 383 Z" fill="#0f4825" />
        <path d="M205 408 L235 448 L255 428 Z" fill="#b91c1c" />
        <ellipse cx="80" cy="285" rx="20" ry="11" fill="#1db84c" stroke="#2a1102" strokeWidth="4" transform="rotate(-40 80 285)" />
        <line x1="80" y1="285" x2="55" y2="320" stroke="#163820" strokeWidth="12" strokeLinecap="round" />
        <line x1="80" y1="285" x2="55" y2="320" stroke="#2a1102" strokeWidth="3" />

        {/* Head, Eyes, Hat (Animated Bobbing) */}
        <g id="head-group" className="cr-head">
          {/* Round Cookie Head */}
          <circle cx="285" cy="210" r="145" fill="#c98042" stroke="#2a1102" strokeWidth="8" />

          {/* Wide Laughing Grin with Lip Outline & Inner Depth */}
          <path d="M210 205 Q285 245 375 245 C355 315 255 315 210 205 Z" fill="#9e4d1a" />
          <path d="M260 275 Q295 250 330 275 C310 305 280 305 260 275 Z" fill="#e26b6b" />
          <path
            d="M210 205 Q285 245 375 245 C355 315 255 315 210 205 Z"
            fill="none"
            stroke="#ba1e1e"
            strokeWidth="10"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* 1. Character Right Eye (Screen Left) */}
          <g id="eye-left-char">
            <path
              d="M230 148 C280 185 295 205 285 220 C270 240 215 240 200 205 C188 178 200 152 230 148 Z"
              fill="#ffffff"
              stroke="#2a1102"
              strokeWidth="6"
            />
            <path
              d="M245 162 C275 190 280 205 272 216 C262 230 225 230 215 205 C208 185 220 165 245 162 Z"
              fill="#0b7ac5"
            />
            <circle cx="248" cy="192" r="9" fill="#043257" />
            <circle cx="253" cy="186" r="4.5" fill="#ffffff" />
            <circle cx="242" cy="198" r="2.2" fill="#ffffff" opacity="0.85" />
            <path
              d="M205 160 C240 162 285 190 288 205"
              fill="none"
              stroke="#2a1102"
              strokeWidth="8"
              strokeLinecap="round"
            />
          </g>

          {/* 2. Character Left Eye (Screen Right) */}
          <g id="eye-right-char">
            <path
              d="M350 185 C395 205 408 225 402 245 C392 265 350 268 335 240 C322 215 330 190 350 185 Z"
              fill="#ffffff"
              stroke="#2a1102"
              strokeWidth="6"
            />
            <path
              d="M358 198 C388 212 396 226 391 240 C384 254 355 255 345 235 C336 218 342 202 358 198 Z"
              fill="#0b7ac5"
            />
            <circle cx="365" cy="220" r="9" fill="#043257" />
            <circle cx="370" cy="214" r="4.5" fill="#ffffff" />
            <circle cx="360" cy="226" r="2.2" fill="#ffffff" opacity="0.85" />
            <path
              d="M332 200 C365 202 398 220 405 232"
              fill="none"
              stroke="#2a1102"
              strokeWidth="8"
              strokeLinecap="round"
            />
          </g>

          {/* 3. Fierce Icing Eyebrows */}
          <polygon points="225,115 315,188 290,172 270,140" fill="#ffffff" stroke="#2a1102" strokeWidth="4" strokeLinejoin="round" />
          <polygon points="315,188 340,160 375,190 345,198" fill="#ffffff" stroke="#2a1102" strokeWidth="4" strokeLinejoin="round" />

          {/* 4. White Icing Forehead Hair with Trademark Wave */}
          <path
            d="M150 115 C175 135 235 135 285 158 C305 168 312 150 305 138 C280 132 245 112 210 102 C175 92 155 105 150 115 Z"
            fill="#ffffff"
            stroke="#2a1102"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />
          <path
            d="M275 110 C300 125 328 135 348 138 C358 140 365 130 358 122 C342 112 318 102 292 98 Z"
            fill="#ffffff"
            stroke="#2a1102"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />

          {/* 5. Traditional Gat / Swashbuckler Warrior Hat */}
          <g id="warrior-hat" transform="rotate(22 360 85)">
            <ellipse cx="350" cy="85" rx="122" ry="48" fill="#8da320" stroke="#2a1102" strokeWidth="6" />
            <ellipse cx="350" cy="83" rx="112" ry="40" fill="#1a2e20" stroke="#2a1102" strokeWidth="5" />
            <path d="M280 72 C280 12 420 12 420 72 Z" fill="#1a2e20" stroke="#2a1102" strokeWidth="6" />
            <path
              d="M365 52 C350 42 338 52 346 62 C356 70 372 65 372 54 C372 38 348 36 338 46"
              fill="none"
              stroke="#a5c828"
              strokeWidth="7"
              strokeLinecap="round"
            />
            <ellipse cx="278" cy="65" rx="14" ry="18" fill="#ffffff" stroke="#2a1102" strokeWidth="3.5" transform="rotate(-28 278 65)" />
            <ellipse cx="304" cy="85" rx="15" ry="19" fill="#ffffff" stroke="#2a1102" strokeWidth="3.5" transform="rotate(-15 304 85)" />
            <ellipse cx="336" cy="100" rx="16" ry="20" fill="#ffffff" stroke="#2a1102" strokeWidth="3.5" />
            <ellipse cx="372" cy="103" rx="16" ry="20" fill="#ffffff" stroke="#2a1102" strokeWidth="3.5" transform="rotate(12 372 103)" />
            <ellipse cx="408" cy="94" rx="14" ry="18" fill="#ffffff" stroke="#2a1102" strokeWidth="3.5" transform="rotate(25 408 94)" />
          </g>
        </g>

        {/* Right Hand Grasping Forward & Raised Sword (Animated Thrust & Slash) */}
        <g id="cookie-sword-arm" className="cr-sword-arm">
          <path
            d="M310 335 C335 300 375 280 405 315 C418 345 388 385 330 380 Z"
            fill="#c98042"
            stroke="#2a1102"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <g id="sword-right">
            <path d="M380 290 L515 180" stroke="#2a1102" strokeWidth="18" strokeLinecap="round" />
            <path d="M380 290 L515 180" stroke="#ffffff" strokeWidth="12" strokeLinecap="round" />
            <polygon points="410,265 432,248 420,270" fill="#0f4825" />
            <polygon points="440,240 462,223 450,245" fill="#b91c1c" />
            <polygon points="470,215 492,198 480,220" fill="#0f4825" />
            <ellipse cx="380" cy="290" rx="18" ry="10" fill="#1db84c" stroke="#2a1102" strokeWidth="4" transform="rotate(45 380 290)" />
          </g>
        </g>
      </g>
    </svg>
  );
};

// Aliases for seamless imports across the app
export const CookieHeroIcon: React.FC<IconProps> = CookieWarriorHeroIcon;
export const CandyCastleIcon: React.FC<IconProps> = CookieWarriorHeroIcon;

/**
 * Star Sugar Jelly Vector Icon
 */
export const StarJellyIcon: React.FC<IconProps> = ({ className = 'w-5 h-5', size = 22 }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <radialGradient id="starGlow" cx="40%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#FEF9C3" />
          <stop offset="50%" stopColor="#FBBF24" />
          <stop offset="100%" stopColor="#D97706" />
        </radialGradient>
      </defs>
      <path
        d="M12 2L14.9 8.2L21.7 9.1L16.7 13.8L18 20.6L12 17.3L6 20.6L7.3 13.8L2.3 9.1L9.1 8.2L12 2Z"
        fill="url(#starGlow)"
        stroke="#B45309"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="10" cy="11" r="1" fill="#FFFFFF" />
      <path d="M11 14C12 15 13 15 14 14" stroke="#78350F" strokeWidth="1" strokeLinecap="round" />
    </svg>
  );
};

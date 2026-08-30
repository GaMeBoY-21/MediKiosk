// Owner: Ranjith
// Inline SVG, single colour (currentColor), drawn simply, 64px by default.
// An icon is NEVER a control on its own — every use is paired with a text
// label and spoken audio. These are all aria-hidden for that reason.

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

function Svg({ size = 64, children, ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
      {...base}
      {...rest}
    >
      {children}
    </svg>
  );
}

/* ------------------------------------------------------------ navigation */

export const HandTouch = (p) => (
  <Svg {...p}>
    <path d="M9 11V5.5a1.5 1.5 0 0 1 3 0V11" />
    <path d="M12 11V4.5a1.5 1.5 0 0 1 3 0V11" />
    <path d="M15 11V6.5a1.5 1.5 0 0 1 3 0V13" />
    <path d="M9 11V9.5a1.5 1.5 0 0 0-3 0V15c0 3.3 2.7 6 6 6h1.5c3 0 5.5-2.5 5.5-5.5V13" />
  </Svg>
);

export const ArrowLeft = (p) => (
  <Svg {...p}>
    <path d="M19 12H5" />
    <path d="M12 19l-7-7 7-7" />
  </Svg>
);

export const Speaker = (p) => (
  <Svg {...p}>
    <path d="M4 9v6h4l5 4V5L8 9H4z" />
    <path d="M17 8.5a5 5 0 0 1 0 7" />
    <path d="M19.5 6a8 8 0 0 1 0 12" />
  </Svg>
);

export const Mic = (p) => (
  <Svg {...p}>
    <rect x="9" y="2" width="6" height="12" rx="3" />
    <path d="M5 11a7 7 0 0 0 14 0" />
    <path d="M12 18v4" />
  </Svg>
);

export const Check = (p) => (
  <Svg {...p}>
    <path d="M4 12.5l5.5 5.5L20 7" />
  </Svg>
);

export const Cross = (p) => (
  <Svg {...p}>
    <path d="M6 6l12 12" />
    <path d="M18 6L6 18" />
  </Svg>
);

export const Pencil = (p) => (
  <Svg {...p}>
    <path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4z" />
    <path d="M14 6l4 4" />
  </Svg>
);

export const Camera = (p) => (
  <Svg {...p}>
    <path d="M3 8h3l2-3h8l2 3h3v11H3V8z" />
    <circle cx="12" cy="13" r="4" />
  </Svg>
);

export const Document = (p) => (
  <Svg {...p}>
    <path d="M14 3H6v18h12V7l-4-4z" />
    <path d="M14 3v4h4" />
    <path d="M9 13h6" />
    <path d="M9 17h6" />
  </Svg>
);

export const IdCard = (p) => (
  <Svg {...p}>
    <rect x="2" y="5" width="20" height="14" rx="2" />
    <circle cx="8" cy="11" r="2.2" />
    <path d="M4.5 16.5c.7-1.6 2-2.4 3.5-2.4s2.8.8 3.5 2.4" />
    <path d="M15 10h4" />
    <path d="M15 14h4" />
  </Svg>
);

export const Person = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" />
  </Svg>
);

export const Warning = (p) => (
  <Svg {...p}>
    <path d="M12 3L2 20h20L12 3z" />
    <path d="M12 10v4" />
    <path d="M12 17.5v.01" />
  </Svg>
);

/* ------------------------------------------------------------- body areas */

export const Head = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="9" r="6" />
    <path d="M7 20c0-2.5 2.2-4 5-4s5 1.5 5 4" />
  </Svg>
);

export const Chest = (p) => (
  <Svg {...p}>
    <path d="M12 21c-4-2.5-7-5.6-7-9.2A4 4 0 0 1 12 9a4 4 0 0 1 7 2.8c0 3.6-3 6.7-7 9.2z" />
  </Svg>
);

export const Stomach = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8" />
    <path d="M9 12c1.2-1.6 4.8-1.6 6 0" />
    <path d="M12 8.5v-2" />
  </Svg>
);

export const BackBody = (p) => (
  <Svg {...p}>
    <path d="M12 3v18" />
    <path d="M9 6h6" />
    <path d="M9 10h6" />
    <path d="M9 14h6" />
    <path d="M9 18h6" />
  </Svg>
);

export const Joints = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.5" />
    <path d="M12 3v5.5" />
    <path d="M12 15.5V21" />
    <path d="M5 7l3.5 3" />
    <path d="M19 17l-3.5-3" />
  </Svg>
);

export const Skin = (p) => (
  <Svg {...p}>
    <rect x="3.5" y="3.5" width="17" height="17" rx="3" />
    <circle cx="9" cy="9" r="1.2" />
    <circle cx="15" cy="11" r="1.2" />
    <circle cx="10.5" cy="15.5" r="1.2" />
  </Svg>
);

export const Fever = (p) => (
  <Svg {...p}>
    <path d="M13 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z" />
    <path d="M17 6h4" />
    <path d="M17 10h3" />
  </Svg>
);

export const Breathing = (p) => (
  <Svg {...p}>
    <path d="M12 4v7" />
    <path d="M12 11c0 4-3 4-3 7a2.5 2.5 0 0 1-5 0c0-5 3-7 3-11" />
    <path d="M12 11c0 4 3 4 3 7a2.5 2.5 0 0 0 5 0c0-5-3-7-3-11" />
  </Svg>
);

export const Other = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M9.5 9.5a2.6 2.6 0 0 1 5 .8c0 1.8-2.5 2-2.5 3.7" />
    <path d="M12 17.5v.01" />
  </Svg>
);

/* ------------------------------------------------------------------- sex */

export const Male = (p) => (
  <Svg {...p}>
    <circle cx="10" cy="14" r="6" />
    <path d="M15 9l5-5" />
    <path d="M15 4h5v5" />
  </Svg>
);

export const Female = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="9" r="6" />
    <path d="M12 15v6" />
    <path d="M9 18h6" />
  </Svg>
);

export const OtherSex = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="13" r="5.5" />
    <path d="M16 9l4-4" />
    <path d="M16 5h4v4" />
    <path d="M12 18.5V22" />
    <path d="M10 20.5h4" />
  </Svg>
);

// Named map so screens can look an icon up from API/config data by string.
export const ICONS = {
  head: Head,
  chest: Chest,
  stomach: Stomach,
  back: BackBody,
  joints: Joints,
  skin: Skin,
  fever: Fever,
  breathing: Breathing,
  other: Other,
  male: Male,
  female: Female,
  otherSex: OtherSex,
  abha: IdCard,
  aadhaar: IdCard,
  newHere: Person,
  document: Document,
  camera: Camera,
  check: Check,
};

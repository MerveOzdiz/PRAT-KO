// frontend/src/Logo.js

import React from 'react';

function Logo() {
  return (
    <svg
      width="48" // Logonun genişliğini buradan ayarlayabilirsiniz
      height="48" // Logonun yüksekliğini buradan ayarlayabilirsiniz
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Yeşil Fiyat Etiketi Gövdesi */}
      <path
        d="M94.1,36.5L63.5,5.9C61.1,3.5,57.9,3.5,55.5,5.9L5.9,55.5c-2.4,2.4-2.4,6.1,0,8.5l29.6,29.6c2.4,2.4,6.1,2.4,8.5,0l49.6-49.6C96.5,42.6,96.5,38.9,94.1,36.5z"
        fill="#5fab71ff" // Tasarrufu simgeleyen yeşil renk
      />
      {/* Etiketin Deliği */}
      <circle cx="27" cy="27" r="7" fill="white"/>

      {/* Beyaz Onay İşareti */}
      <polyline
        points="40,55 55,70 80,40"
        fill="none"
        stroke="white"
        strokeWidth="10"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default Logo;
import React from "react";

/**
 * Authentic SVG Icons extracted directly from the Figma Prototype design files.
 * Provides pixel-perfect vector geometry for the Raspberry Pi / Chromium kiosk.
 */

// 1. Logo / Scanner Barcode Frame
export function FigmaBarcode({ className = "w-6 h-6", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M0 5.33V2.67C0 1.96 0.28 1.28 0.78 0.78C1.28 0.28 1.96 0 2.67 0H5.33M18.67 0H21.33C22.04 0 22.72 0.28 23.22 0.78C23.72 1.28 24 1.96 24 2.67V5.33M24 18.67V21.33C24 22.04 23.72 22.72 23.22 23.22C22.72 23.72 22.04 24 21.33 24H18.67M5.33 24H2.67C1.96 24 1.28 23.72 0.78 23.22C0.28 22.72 0 22.04 0 21.33V18.67M6.67 5.33V18.67M12 5.33V18.67M18.67 5.33V18.67" />
    </svg>
  );
}

// 2. Home Button Icon
export function FigmaHome({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M15.25 21.25V12.58C15.25 12.3 15.14 12.02 14.93 11.82C14.73 11.61 14.45 11.5 14.17 11.5H9.83C9.55 11.5 9.27 11.61 9.07 11.82C8.86 12.02 8.75 12.3 8.75 12.58V21.25M2.25 9.33C2.25 9.02 2.32 8.71 2.45 8.42C2.58 8.13 2.78 7.88 3.02 7.68L10.6 1.18C10.99 0.85 11.49 0.67 12 0.67C12.51 0.67 13.01 0.85 13.4 1.18L20.98 7.68C21.22 7.88 21.42 8.13 21.55 8.42C21.68 8.71 21.75 9.02 21.75 9.33V19.08C21.75 19.66 21.52 20.21 21.12 20.62C20.71 21.02 20.16 21.25 19.58 21.25H4.42C3.84 21.25 3.29 21.02 2.88 20.62C2.48 20.21 2.25 19.66 2.25 19.08V9.33Z" />
    </svg>
  );
}

// 3. Search Magnifier Icon
export function FigmaSearch({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M21.75 21.75L17.05 17.05M19.58 10.92C19.58 15.7 15.7 19.58 10.92 19.58C6.13 19.58 2.25 15.7 2.25 10.92C2.25 6.13 6.13 2.25 10.92 2.25C15.7 2.25 19.58 6.13 19.58 10.92Z" />
    </svg>
  );
}

// 4. Cart Icon
export function FigmaCart({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M1 2H5L7.68 15.39C7.771 15.85 8.022 16.264 8.388 16.559C8.753 16.853 9.211 17.009 9.68 17H19.4C19.869 17.009 20.327 16.853 20.692 16.559C21.058 16.264 21.309 15.85 21.4 15.39L23 7H6M10 22C10 22.552 9.552 23 9 23C8.448 23 8 22.552 8 22C8 21.448 8.448 21 9 21C9.552 21 10 21.448 10 22ZM21 22C21 22.552 20.552 23 20 23C19.448 23 19 22.552 19 22C19 21.448 19.448 21 20 21C20.552 21 21 21.448 21 22Z" />
    </svg>
  );
}

// 5. Nutrition (Pie Chart) Icon
export function FigmaNutrition({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M21.21 15.89C20.574 17.394 19.579 18.72 18.312 19.751C17.045 20.782 15.545 21.487 13.942 21.805C12.34 22.122 10.684 22.042 9.12 21.572C7.556 21.102 6.13 20.255 4.969 19.107C3.807 17.958 2.945 16.543 2.457 14.984C1.968 13.425 1.87 11.77 2.169 10.165C2.468 8.56 3.155 7.051 4.172 5.772C5.189 4.493 6.503 3.483 8 2.83M22 12C22 10.687 21.741 9.386 21.239 8.173C20.736 6.96 20 5.858 19.071 4.929C18.142 4 17.04 3.264 15.827 2.761C14.614 2.259 13.313 2 12 2V12H22Z" />
    </svg>
  );
}

// 6. Edit (Pencil) Icon
export function FigmaEdit({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M15.25 4.42L19.58 8.75M21.94 6.38C22.51 5.81 22.83 5.03 22.83 4.22C22.83 3.41 22.51 2.63 21.94 2.06C21.37 1.49 20.59 1.17 19.78 1.17C18.97 1.17 18.19 1.49 17.62 2.06L3.16 16.52C2.91 16.77 2.72 17.08 2.62 17.42L1.19 22.14C1.16 22.23 1.16 22.33 1.18 22.42C1.21 22.52 1.26 22.6 1.32 22.67C1.39 22.74 1.48 22.79 1.58 22.82C1.67 22.84 1.77 22.84 1.86 22.81L6.58 21.38C6.92 21.28 7.23 21.09 7.48 20.84L21.94 6.38Z" />
    </svg>
  );
}

// 7. Delete (Trash) Icon
export function FigmaTrash({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M6.58 21.75C5.99 21.75 5.48 21.54 5.05 21.11C4.63 20.69 4.42 20.18 4.42 19.58V5.5H3.33V3.33H8.75V2.25H15.25V3.33H20.67V5.5H19.58V19.58C19.58 20.18 19.37 20.69 18.95 21.11C18.52 21.54 18.01 21.75 17.42 21.75H6.58ZM17.42 5.5H6.58V19.58H17.42V5.5ZM8.75 17.42H10.92V7.67H8.75V17.42ZM13.08 17.42H15.25V7.67H13.08V17.42Z" />
    </svg>
  );
}

// 8. Stepper Minus Icon
export function FigmaMinus({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <rect x="4.5" y="10.75" width="15" height="2.5" rx="1.25" />
    </svg>
  );
}

// 9. Stepper Plus Icon
export function FigmaPlus({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M10.75 19.25H13.25V13.25H19.25V10.75H13.25V4.75H10.75V10.75H4.75V13.25H10.75V19.25Z" />
    </svg>
  );
}

// 10. Chevron Down Icon (Footer scroll & dropdowns)
export function FigmaChevronDown({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 15.4L6 9.4L7.4 8L12 12.6L16.6 8L18 9.4L12 15.4Z" />
    </svg>
  );
}

// 11. Undo Return Arrow Icon (from Barcode Scan Feedback)
export function FigmaUndo({ className = "w-6 h-6", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M5.33 21.83V19.17H14.8C16.2 19.17 17.42 18.72 18.45 17.83C19.48 16.94 20 15.83 20 14.5C20 13.17 19.48 12.06 18.45 11.17C17.42 10.28 16.2 9.83 14.8 9.83H6.4L9.87 13.3L8 15.17L1.33 8.5L8 1.83L9.87 3.7L6.4 7.17H14.8C16.96 7.17 18.81 7.87 20.35 9.27C21.89 10.67 22.67 12.41 22.67 14.5C22.67 16.59 21.89 18.33 20.35 19.73C18.81 21.13 16.96 21.83 14.8 21.83H5.33Z" />
    </svg>
  );
}

// 12. Checkmark Icon (from Barcode Scan Feedback green badge)
export function FigmaCheckmark({ className = "w-8 h-8", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M8.33 20.5L0 12L2.14 9.81L8.33 16.23L22.09 2.46L24.23 4.6L8.33 20.5Z" />
    </svg>
  );
}

// 13. Close Icon
export function FigmaClose({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12Z" />
    </svg>
  );
}

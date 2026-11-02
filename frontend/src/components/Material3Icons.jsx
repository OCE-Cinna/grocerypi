import React from "react";

/**
 * Official Google Material 3 Design Kit SVG Icons & Symbols
 * Crisp 24x24 vector paths designed for Material 3 / Chromium kiosk display.
 */

// 0. Generic Material Symbol component (uses the installed material-symbols font)
export function MaterialSymbol({ icon, className = "", style = {}, ...props }) {
  return (
    <span
      className={`material-symbols-rounded select-none leading-none inline-flex items-center justify-center shrink-0 ${className}`}
      style={{ fontVariationSettings: "'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 24", ...style }}
      aria-hidden="true"
      {...props}
    >
      {icon}
    </span>
  );
}

// 1. App Logo / Scanner Barcode Frame (Material 3 barcode_scanner)
export function M3BarcodeScanner({ className = "w-6 h-6", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M2 4a2 2 0 0 1 2-2h4a1 1 0 0 1 0 2H4v4a1 1 0 0 1-2 0V4zm18-2a2 2 0 0 1 2 2v4a1 1 0 0 1-2 0V4h-4a1 1 0 0 1 0-2h4zM2 20a2 2 0 0 0 2 2h4a1 1 0 0 0 0-2H4v-4a1 1 0 0 0-2 0v4zm20 0a2 2 0 0 1-2 2h-4a1 1 0 0 1 0-2h4v-4a1 1 0 0 1 2 0v4zM6 7a1 1 0 0 1 2 0v10a1 1 0 0 1-2 0V7zm4 0a1 1 0 0 1 1 0v10a1 1 0 0 1-1 0V7zm3 0a1 1 0 0 1 2 0v10a1 1 0 0 1-2 0V7zm4 0a1 1 0 0 1 1 0v10a1 1 0 0 1-1 0V7z" />
    </svg>
  );
}

// 2. Vegan Icon (Material 3 eco)
export function M3Eco({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M16.05 4.46C13.95 2.37 10.57 2.07 8.16 3.77L15.34 11l-1.41 1.41L6.75 5.22C5.05 7.63 5.35 11.01 7.44 13.11c2.19 2.19 5.56 2.39 7.99.63l-4.14-4.14 1.41-1.41 4.14 4.14c1.76-2.43 1.56-5.8-.79-7.97z" />
    </svg>
  );
}

// 3. Vegetarian Icon (Material 3 spa)
export function M3Spa({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 2c-1.35 2.02-3.5 3.6-6 4.25.9 2.45 2.65 4.5 5 5.75V2zm1 0v10c2.35-1.25 4.1-3.3 5-5.75-2.5-.65-4.65-2.23-6-4.25zm-2 12.5C6.55 14 3.1 16.35 2 20c3.65-1.1 6-4.55 6-7.5h3zm2 0h3c0 2.95 2.35 6.4 6 7.5-1.1-3.65-4.55-6-9-7.5z" />
    </svg>
  );
}

// 4. Home (Material 3 home)
export function M3Home({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M10.7 2.3a2 2 0 0 1 2.6 0l7 5.8a2 2 0 0 1 .7 1.5V19a2 2 0 0 1-2 2h-4a1 1 0 0 1-1-1v-5a1 1 0 0 0-1-1h-2a1 1 0 0 0-1 1v5a1 1 0 0 1-1 1H5a2 2 0 0 1-2-2V9.6a2 2 0 0 1 .7-1.5l7-5.8z" />
    </svg>
  );
}

// 5. Shopping Cart (Material 3 shopping_cart)
export function M3Cart({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zm10 0c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2zm-9.83-3.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.86-7.01L19.42 4h-.01l-1.1 2-2.76 5H8.53l-.13-.27L6.16 6l-.95-2-.94-2H1v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.13 0-.25-.11-.25-.25z" />
    </svg>
  );
}

// 6. Nutrition (Figma Prototype Sliced Pie Chart Icon)
export function M3Nutrition({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M21.21 15.89C20.574 17.394 19.579 18.72 18.312 19.751C17.045 20.782 15.545 21.487 13.942 21.805C12.34 22.122 10.684 22.042 9.12 21.572C7.556 21.102 6.13 20.255 4.969 19.107C3.807 17.958 2.945 16.543 2.457 14.984C1.968 13.425 1.87 11.77 2.169 10.165C2.468 8.56 3.155 7.051 4.172 5.772C5.189 4.493 6.503 3.483 8 2.83M22 12C22 10.687 21.741 9.386 21.239 8.173C20.736 6.96 20 5.858 19.071 4.929C18.142 4 17.04 3.264 15.827 2.761C14.614 2.259 13.313 2 12 2V12H22Z" />
    </svg>
  );
}

// 7. Search (Material 3 search)
export function M3Search({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
    </svg>
  );
}

// 8. Add / Plus (Material 3 add)
export function M3Add({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M18 13h-5v5a1 1 0 0 1-2 0v-5H6a1 1 0 0 1 0-2h5V6a1 1 0 0 1 2 0v5h5a1 1 0 0 1 0 2z" />
    </svg>
  );
}

// 9. Remove / Minus (Material 3 remove)
export function M3Remove({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M18 13H6a1 1 0 0 1 0-2h12a1 1 0 0 1 0 2z" />
    </svg>
  );
}

// 10. Edit / Pencil (Material 3 edit)
export function M3Edit({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
    </svg>
  );
}

// 11. Delete / Trash (Material 3 delete)
export function M3Trash({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
    </svg>
  );
}

// 12. Close / Clear (Material 3 close)
export function M3Close({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

// 13. Checkmark (Material 3 check)
export function M3Check({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

// 14. Check Circle (Material 3 check_circle)
export function M3CheckCircle({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
    </svg>
  );
}

// 15. Undo (Material 3 undo)
export function M3Undo({ className = "w-6 h-6", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z" />
    </svg>
  );
}

// 16. Chevron Down (Material 3 expand_more)
export function M3ChevronDown({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
    </svg>
  );
}

// 17. Video Preview On (Material 3 videocam)
export function M3Videocam({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M17 10.5V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-3.5l4 4a1 1 0 0 0 1.6-.8v-9.4a1 1 0 0 0-1.6-.8l-4 4z" />
    </svg>
  );
}

// 18. Video Preview Off (Material 3 videocam_off)
export function M3VideocamOff({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M21 6.5l-4 4V7c0-.55-.45-1-1-1H9.82L21 17.18V6.5zM3.27 2L2 3.27 4.73 6H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.21 0 .39-.08.54-.18L19.73 21 21 19.73 3.27 2zM16 16H6.27l8-8H16v8z" />
    </svg>
  );
}

// 19. Celebration (Material 3 celebration)
export function M3Celebration({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M2 22l14-5-9-9-5 14zm4.03-3.03l1.8-5.06 3.26 3.26-5.06 1.8zM20 6c0-1.1-.9-2-2-2s-2 .9-2 2 .9 2 2 2 2-.9 2-2zm-3.5 7c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5-1.5.67-1.5 1.5.67 1.5 1.5 1.5zm5-5c.83 0 1.5-.67 1.5-1.5S22.33 5 21.5 5 20 5.67 20 6.5s.67 1.5 1.5 1.5zM22 12c0-.55-.45-1-1-1s-1 .45-1 1 .45 1 1 1 1-.45 1-1zm-9.5-8c.55 0 1-.45 1-1s-.45-1-1-1-1 .45-1 1 .45 1 1 1z" />
    </svg>
  );
}

// 20. Refresh (Material 3 refresh)
export function M3Refresh({ className = "w-4 h-4", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
    </svg>
  );
}

// 21. Arrow Back (Material 3 arrow_back)
export function M3ArrowBack({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
    </svg>
  );
}

// 22. Package / Inventory (Material 3 inventory_2)
export function M3Package({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M20 2H4c-1 0-2 .9-2 2v3.01c0 .72.43 1.34 1 1.69V20c0 1.1 1.1 2 2 2h14c.9 0 2-.9 2-2V8.7c.57-.35 1-.97 1-1.69V4c0-1.1-1-2-2-2zm-5 12H9v-2h6v2zm5-7H4V4h16v3z" />
    </svg>
  );
}

// 23. Circle / Radio Unchecked (Material 3 radio_button_unchecked)
export function M3Circle({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z" />
    </svg>
  );
}

// 24. Loader / Progress Spinner (Material 3 progress_activity)
export function M3Loader({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 animate-spin ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z" opacity="0.3"/>
      <path d="M12 2a10 10 0 0 1 10 10h-2a8 8 0 0 0-8-8V2z"/>
    </svg>
  );
}

// 25. Eye / Visibility (Material 3 visibility)
export function M3Visibility({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
    </svg>
  );
}

// 26. Eye Off / Visibility Off (Material 3 visibility_off)
export function M3VisibilityOff({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.44-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z" />
    </svg>
  );
}

// 27. Bar Chart (Material 3 bar_chart)
export function M3BarChart({ className = "w-5 h-5", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
      {...props}
    >
      <path d="M4 9h4v11H4zm6-5h4v16h-4zm6 8h4v8h-4z" />
    </svg>
  );
}

// Re-exports matching legacy names for compatibility
export {
  M3BarcodeScanner as FigmaBarcode,
  M3Home as FigmaHome,
  M3Cart as FigmaCart,
  M3Nutrition as FigmaNutrition,
  M3Search as FigmaSearch,
  M3Edit as FigmaEdit,
  M3Trash as FigmaTrash,
  M3Remove as FigmaMinus,
  M3Add as FigmaPlus,
  M3ChevronDown as FigmaChevronDown,
  M3Undo as FigmaUndo,
  M3CheckCircle as FigmaCheckmark,
  M3Close as FigmaClose,
  M3Eco as EcoIcon,
  M3Spa as SpaIcon,
  M3CheckCircle as CheckCircleIcon,
  M3Celebration as CelebrationIcon,
  M3Close as CloseIcon,
};

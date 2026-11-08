import { type ReactNode, createContext, useContext } from "react";

export type ShowToast = (content: ReactNode) => void;
export const ToastContext = createContext<ShowToast>(() => {});
export const useToast = (): ShowToast => useContext(ToastContext);

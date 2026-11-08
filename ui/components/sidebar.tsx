"use client";

import { type ReactNode, useState } from "react";

export type PageView = "review" | "settings";

type Props = {
  activeView: PageView;
  onViewChange: (view: PageView) => void;
};

type NavigationItem = {
  view: PageView;
  label: string;
  icon: ReactNode;
};

const navigationItems: NavigationItem[] = [
  {
    view: "review",
    label: "Review",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
        className="h-5 w-5 shrink-0"
      >
        <path
          d="m16 18 6-6-6-6M8 6l-6 6 6 6"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    view: "settings",
    label: "Settings",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
        className="h-5 w-5 shrink-0"
      >
        <g
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.09a2 2 0 0 1-1-1.74v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2Z" />
          <circle cx="12" cy="12" r="3" />
        </g>
      </svg>
    ),
  },
];

export default function Sidebar({ activeView, onViewChange }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  function toggleSidebar() {
    setCollapsed((value) => !value);
  }

  return (
    <aside
      className="flex min-h-dvh shrink-0 flex-col border-r border-black/[0.06] bg-white transition-[width] duration-300"
      style={{ width: collapsed ? 40 : 132 }}
    >
      <div className={`flex p-2 ${collapsed ? "justify-center px-1" : "justify-end"}`}>
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand" : "Collapse"}
          className="grid h-8 w-8 place-items-center rounded-md text-neutral-400 hover:bg-neutral-100 hover:text-neutral-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/20"
        >
          <svg
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
            className="h-5 w-5"
          >
            <rect
              x="2.25"
              y="3.25"
              width="11.5"
              height="9.5"
              rx="2"
              stroke="currentColor"
              strokeWidth="1.3"
            />
            <path
              d="M6.25 3.25v9.5"
              stroke="currentColor"
              strokeWidth="1.3"
            />
          </svg>
        </button>
      </div>

      <nav
        aria-label="Main navigation"
        className={`flex flex-1 flex-col py-2 ${collapsed ? "px-1" : "px-2"}`}
      >
        <ul className="flex flex-1 flex-col gap-1">
          {navigationItems.map((item) => {
            const isActive = activeView === item.view;

            return (
              <li key={item.view} className={item.view === "settings" ? "mt-auto" : undefined}>
                <button
                  type="button"
                  onClick={() => onViewChange(item.view)}
                  aria-label={item.label}
                  aria-current={isActive ? "page" : undefined}
                  title={item.label}
                  className={`flex h-9 w-full items-center rounded-md text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/20 ${
                    collapsed ? "justify-center" : "gap-3 px-3"
                  } ${
                    isActive
                      ? "bg-neutral-100 text-neutral-900"
                      : "text-neutral-500 hover:bg-neutral-50 hover:text-neutral-900"
                  }`}
                >
                  {item.icon}
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}

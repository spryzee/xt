
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  LayoutDashboard,
  Server,
  Users,
  LineChart,
  Settings,
  CreditCard,
  LogOut
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarLinkProps {
  path: string;
  icon: JSX.Element;
  label: string;
  isActive: boolean;
}

const SidebarLink = ({ path, icon, label, isActive }: SidebarLinkProps) => {
  return (
    <Link 
      to={path} 
      className={cn(
        "flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-200",
        isActive 
          ? "bg-primary text-white" 
          : "text-gray-300 hover:bg-white/5"
      )}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </Link>
  );
};

export default function Sidebar() {
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  // Mocking authentication for our UI
  const handleLogin = () => {
    setIsLoggedIn(true);
  };
  
  const links = [
    { path: "/dashboard", label: "Dashboard", icon: <LayoutDashboard size={20} /> },
    { path: "/servers", label: "Servers", icon: <Server size={20} /> },
    { path: "/users", label: "Users", icon: <Users size={20} /> },
    { path: "/analytics", label: "Analytics", icon: <LineChart size={20} /> },
    { path: "/pricing", label: "Pricing", icon: <CreditCard size={20} /> },
    { path: "/settings", label: "Settings", icon: <Settings size={20} /> },
  ];

  return (
    <div className="h-screen w-64 bg-secondary border-r border-white/10 flex flex-col">
      <div className="p-4 flex items-center gap-3 border-b border-white/10">
        <div className="w-10 h-10 rounded-md bg-primary flex items-center justify-center">
          <span className="text-xl font-bold">XT</span>
        </div>
        <h1 className="text-xl font-bold">XTLive</h1>
      </div>

      {isLoggedIn ? (
        <>
          <div className="p-4 space-y-1">
            {links.map((link) => (
              <SidebarLink 
                key={link.path}
                path={link.path}
                icon={link.icon}
                label={link.label}
                isActive={location.pathname === link.path}
              />
            ))}
          </div>
          
          <div className="mt-auto p-4 border-t border-white/10">
            <button 
              className="flex items-center gap-3 px-4 py-3 w-full rounded-md text-red-400 hover:bg-red-400/10 transition-all"
              onClick={() => setIsLoggedIn(false)}
            >
              <LogOut size={20} />
              <span className="font-medium">Log Out</span>
            </button>
          </div>
        </>
      ) : (
        <div className="p-4 flex-1 flex items-center justify-center">
          <div className="w-full max-w-xs space-y-4 text-center">
            <h2 className="text-xl font-medium">Welcome to XTLive</h2>
            <p className="text-sm text-gray-400">Sign in with Discord to manage your bots and servers</p>
            <button 
              className="w-full py-2.5 px-4 bg-discord hover:bg-discord-hover transition-colors rounded flex items-center justify-center gap-2"
              onClick={handleLogin}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.27 5.33C17.94 4.71 16.5 4.26 15 4a.09.09 0 0 0-.07.03c-.18.33-.39.76-.53 1.09a16.09 16.09 0 0 0-4.8 0c-.14-.34-.35-.76-.54-1.09-.01-.02-.04-.03-.07-.03-1.5.26-2.93.71-4.27 1.33-.01 0-.02.01-.03.02-2.72 4.07-3.47 8.03-3.1 11.95 0 .02.01.04.03.05 1.8 1.32 3.53 2.12 5.24 2.65.03.01.06 0 .07-.02.4-.55.76-1.13 1.07-1.74.02-.04 0-.08-.04-.09-.57-.22-1.11-.48-1.64-.78-.04-.02-.04-.08-.01-.11.11-.08.22-.17.33-.25.02-.02.05-.02.07-.01 3.44 1.57 7.15 1.57 10.55 0 .02-.01.05-.01.07.01.11.09.22.17.33.26.04.03.04.09-.01.11-.52.31-1.07.56-1.64.78-.04.01-.05.06-.04.09.32.61.68 1.19 1.07 1.74.03.02.06.03.09.02 1.72-.53 3.45-1.33 5.25-2.65.02-.01.03-.03.03-.05.44-4.53-.73-8.46-3.1-11.95-.01-.01-.02-.02-.04-.02zM8.52 14.91c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12 0 1.17-.84 2.12-1.89 2.12zm6.97 0c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12 0 1.17-.83 2.12-1.89 2.12z" />
              </svg>
              <span className="font-medium">Login with Discord</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

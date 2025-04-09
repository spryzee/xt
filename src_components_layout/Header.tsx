
import { useState } from "react";
import { Bell, Search, User, LogOut } from "lucide-react";
import { Input } from "@/components/ui/input";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";

interface HeaderProps {
  onLogout: () => void;
}

export default function Header({ onLogout }: HeaderProps) {
  const [notifications, setNotifications] = useState([
    { id: 1, title: "Server Update", message: "Astro Bot went offline", time: "2m ago" },
    { id: 2, title: "New User", message: "User FrostByte joined the server", time: "10m ago" },
    { id: 3, title: "System Alert", message: "Database backup completed", time: "1h ago" },
  ]);
  
  return (
    <header className="h-16 border-b border-white/10 flex items-center justify-between px-6">
      <div className="w-72">
        <div className="relative">
          <Search size={18} className="absolute left-2.5 top-2.5 text-gray-400" />
          <Input
            placeholder="Search..."
            className="pl-9 bg-secondary border-none h-9 focus-visible:ring-1 focus-visible:ring-offset-0"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger className="relative focus:outline-none">
            <div className="p-1.5 rounded-md hover:bg-white/5 transition-colors">
              <Bell size={20} />
              <span className="absolute top-0 right-0 w-2 h-2 rounded-full bg-red-500" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {notifications.map(notification => (
              <DropdownMenuItem key={notification.id} className="p-3 cursor-pointer">
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-sm">{notification.title}</p>
                    <span className="text-xs text-muted-foreground">{notification.time}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{notification.message}</p>
                </div>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem className="justify-center">
              <span className="text-sm text-primary">View all notifications</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="focus:outline-none flex items-center gap-2 group">
              <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                <User size={18} />
              </div>
              <span className="text-sm font-medium group-hover:text-primary transition-colors">Admin</span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              className="text-red-500 flex items-center gap-2" 
              onClick={onLogout}
            >
              <LogOut size={16} />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

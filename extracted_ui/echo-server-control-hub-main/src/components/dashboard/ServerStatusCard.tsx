
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { MoreHorizontal, Play, StopCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface ServerStatusCardProps {
  server: {
    id: string;
    name: string;
    status: "online" | "offline" | "idle";
    uptime: string;
    users: number;
    region: string;
    avatar?: string;
  };
  className?: string;
}

export default function ServerStatusCard({ server, className }: ServerStatusCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(server.status);
  
  const handleAction = (action: "start" | "stop" | "restart") => {
    setIsLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      if (action === "start") setCurrentStatus("online");
      else if (action === "stop") setCurrentStatus("offline");
      else if (action === "restart") {
        setCurrentStatus("idle");
        setTimeout(() => setCurrentStatus("online"), 2000);
      }
      
      setIsLoading(false);
    }, 1500);
  };
  
  return (
    <Card className={cn("card-hover", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          {server.avatar ? (
            <img src={server.avatar} alt={server.name} className="w-10 h-10 rounded-full" />
          ) : (
            <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
              <span className="text-lg font-bold">{server.name.charAt(0)}</span>
            </div>
          )}
          <div>
            <CardTitle className="text-base">{server.name}</CardTitle>
            <div className="flex items-center gap-1.5 mt-1">
              <div className={cn("status-indicator",
                currentStatus === "online" && "status-online",
                currentStatus === "offline" && "status-offline",
                currentStatus === "idle" && "status-idle"
              )} />
              <span className="text-xs text-muted-foreground capitalize">{currentStatus}</span>
            </div>
          </div>
        </div>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal size={16} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleAction("start")}>Start</DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleAction("stop")}>Stop</DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleAction("restart")}>Restart</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      
      <CardContent>
        <div className="grid grid-cols-2 gap-4 mt-2">
          <div>
            <p className="text-xs text-muted-foreground">Region</p>
            <p className="font-medium">{server.region}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Users</p>
            <p className="font-medium">{server.users}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Uptime</p>
            <p className="font-medium">{server.uptime}</p>
          </div>
          <div>
            <Badge variant={currentStatus === "online" ? "default" : "outline"} className="mt-1">
              {server.id}
            </Badge>
          </div>
        </div>
        
        <div className="flex items-center gap-2 mt-4">
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1"
            disabled={isLoading || currentStatus === "offline"}
            onClick={() => handleAction("stop")}
          >
            <StopCircle size={16} className="mr-1" />
            Stop
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1"
            disabled={isLoading || currentStatus === "online"}
            onClick={() => handleAction("start")}
          >
            <Play size={16} className="mr-1" />
            Start
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="flex-1"
            disabled={isLoading || currentStatus === "offline"}
            onClick={() => handleAction("restart")}
          >
            <RefreshCw size={16} className={cn("mr-1", isLoading && "animate-spin")} />
            Restart
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}


import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  ArrowDownToLine, 
  ArrowUpToLine, 
  BellRing, 
  UserCheck, 
  UserMinus, 
  UserPlus, 
  MessageSquare 
} from "lucide-react";

interface Activity {
  id: number;
  type: "join" | "leave" | "message" | "notification" | "download" | "upload" | "command";
  user: string;
  server: string;
  time: string;
  message?: string;
}

const getActivityIcon = (type: Activity["type"]) => {
  switch (type) {
    case "join": return <UserPlus size={15} className="text-green-500" />;
    case "leave": return <UserMinus size={15} className="text-red-500" />;
    case "message": return <MessageSquare size={15} className="text-blue-500" />;
    case "notification": return <BellRing size={15} className="text-amber-500" />;
    case "download": return <ArrowDownToLine size={15} className="text-cyan-500" />;
    case "upload": return <ArrowUpToLine size={15} className="text-purple-500" />;
    case "command": return <UserCheck size={15} className="text-indigo-500" />;
  }
};

const activities: Activity[] = [
  { id: 1, type: "join", user: "Frost88", server: "Gaming HQ", time: "3 mins ago" },
  { id: 2, type: "notification", user: "System", server: "Live Bot", time: "10 mins ago", message: "Server restarted" },
  { id: 3, type: "message", user: "Cosmic42", server: "Community", time: "23 mins ago", message: "!help commands" },
  { id: 4, type: "command", user: "Admin", server: "Staff Room", time: "1 hour ago", message: "/kick @spammer" },
  { id: 5, type: "leave", user: "Ninja555", server: "Gaming HQ", time: "2 hours ago" },
  { id: 6, type: "upload", user: "Mod01", server: "Live Bot", time: "3 hours ago", message: "bot-config.json" },
  { id: 7, type: "download", user: "ShadowX", server: "Dashboard", time: "5 hours ago", message: "logs-04-08.txt" },
];

export default function RecentActivity() {
  return (
    <Card className="card-hover">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>The last 24 hours activity across all your servers</CardDescription>
      </CardHeader>
      <CardContent className="max-h-[400px] overflow-y-auto">
        <div className="space-y-4">
          {activities.map((activity) => (
            <div key={activity.id} className="flex gap-3">
              <div className="mt-0.5">{getActivityIcon(activity.type)}</div>
              <div className="space-y-0.5">
                <p className="text-sm">
                  <span className="font-medium">{activity.user}</span>
                  {activity.type === "join" && " joined "}
                  {activity.type === "leave" && " left "}
                  {activity.type === "message" && " sent a message in "}
                  {activity.type === "notification" && " notification in "}
                  {activity.type === "download" && " downloaded from "}
                  {activity.type === "upload" && " uploaded to "}
                  {activity.type === "command" && " used command in "}
                  <span className="font-medium">{activity.server}</span>
                </p>
                {activity.message && (
                  <p className="text-xs text-muted-foreground">{activity.message}</p>
                )}
                <p className="text-xs text-muted-foreground">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

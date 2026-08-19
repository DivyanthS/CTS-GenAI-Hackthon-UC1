import { Link, useNavigate } from "@tanstack/react-router";
import { ChevronDown, LogOut, Settings, User } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth";

function initials(name: string) {
  return name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const signOut = () => {
    logout();
    navigate({ to: "/login" });
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Open account menu"
          className="flex items-center gap-2 rounded-md px-1 py-1 transition-colors hover:bg-accent"
        >
          <span className="grid size-9 place-items-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">
            {initials(user.name)}
          </span>
          <span className="hidden leading-tight sm:block">
            <span className="block text-xs font-medium text-foreground">{user.name}</span>
            <span className="block text-[11px] text-muted-foreground">{user.title}</span>
          </span>
          <ChevronDown className="hidden size-3.5 text-muted-foreground sm:block" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-64">
        <div className="px-2 py-2.5">
          <p className="text-sm font-medium text-foreground">{user.name}</p>
          <p className="text-xs text-muted-foreground">{user.email}</p>
          <p className="mt-1 text-[11px] font-medium text-primary">{user.title}</p>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/profile">
            <User className="size-4" /> Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/settings">
            <Settings className="size-4" /> Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={signOut}>
          <LogOut className="size-4" /> Logout
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

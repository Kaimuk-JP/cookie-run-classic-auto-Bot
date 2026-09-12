import React from 'react';
import {
  Flag,
  Search,
  CheckCircle2,
  Gamepad2,
  Play,
  Square,
  RefreshCw,
  Cookie,
  BarChart3,
  ChevronsUp,
  ChevronsDown,
  Rocket,
  Save,
  Gift,
  Sparkles,
  Home,
  Zap,
  Bell,
  AlertTriangle,
  ArrowRight,
  Trophy,
  Music,
  Coins,
  Star,
  Heart,
  Mail,
  Clock,
  Smartphone,
  Globe,
  Link,
  Target,
  Shield,
  Plug,
  Camera,
  Moon,
  Circle,
  ShoppingCart,
  Dices,
  Hourglass,
  Folder,
} from 'lucide-react';

interface IconConfig {
  icon: React.ComponentType<{ className?: string }>;
  className: string;
}

export const EMOJI_ICON_MAP: Record<string, IconConfig> = {
  '🏁': { icon: Flag, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '🔍': { icon: Search, className: 'w-3.5 h-3.5 text-sky-400 inline shrink-0' },
  '✅': { icon: CheckCircle2, className: 'w-3.5 h-3.5 text-emerald-400 inline shrink-0' },
  '🎮': { icon: Gamepad2, className: 'w-3.5 h-3.5 text-indigo-400 inline shrink-0' },
  '▶️': { icon: Play, className: 'w-3.5 h-3.5 text-emerald-400 fill-current inline shrink-0' },
  '▶': { icon: Play, className: 'w-3.5 h-3.5 text-emerald-400 fill-current inline shrink-0' },
  '⏹️': { icon: Square, className: 'w-3.5 h-3.5 text-rose-400 fill-current inline shrink-0' },
  '⏹': { icon: Square, className: 'w-3.5 h-3.5 text-rose-400 fill-current inline shrink-0' },
  '🔄': { icon: RefreshCw, className: 'w-3.5 h-3.5 text-teal-400 inline shrink-0' },
  '🍪': { icon: Cookie, className: 'w-3.5 h-3.5 text-amber-500 inline shrink-0' },
  '📊': { icon: BarChart3, className: 'w-3.5 h-3.5 text-violet-400 inline shrink-0' },
  '🦘': { icon: ChevronsUp, className: 'w-3.5 h-3.5 text-cyan-400 inline shrink-0' },
  '🛹': { icon: ChevronsDown, className: 'w-3.5 h-3.5 text-pink-400 inline shrink-0' },
  '🚀': { icon: Rocket, className: 'w-3.5 h-3.5 text-indigo-400 inline shrink-0' },
  '💾': { icon: Save, className: 'w-3.5 h-3.5 text-blue-400 inline shrink-0' },
  '🎁': { icon: Gift, className: 'w-3.5 h-3.5 text-yellow-400 inline shrink-0' },
  '🧹': { icon: Sparkles, className: 'w-3.5 h-3.5 text-purple-400 inline shrink-0' },
  '🏠': { icon: Home, className: 'w-3.5 h-3.5 text-slate-400 inline shrink-0' },
  '⚡': { icon: Zap, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '🔔': { icon: Bell, className: 'w-3.5 h-3.5 text-yellow-400 inline shrink-0' },
  '⚠️': { icon: AlertTriangle, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '❌': { icon: AlertTriangle, className: 'w-3.5 h-3.5 text-rose-400 inline shrink-0' },
  '👉': { icon: ArrowRight, className: 'w-3.5 h-3.5 text-slate-400 inline shrink-0' },
  '🎉': { icon: Trophy, className: 'w-3.5 h-3.5 text-amber-300 inline shrink-0' },
  '🏆': { icon: Trophy, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '🎹': { icon: Music, className: 'w-3.5 h-3.5 text-indigo-400 inline shrink-0' },
  '🪙': { icon: Coins, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '⭐': { icon: Star, className: 'w-3.5 h-3.5 text-yellow-400 fill-current inline shrink-0' },
  '💖': { icon: Heart, className: 'w-3.5 h-3.5 text-rose-400 fill-current inline shrink-0' },
  '❤️': { icon: Heart, className: 'w-3.5 h-3.5 text-rose-400 fill-current inline shrink-0' },
  '💌': { icon: Mail, className: 'w-3.5 h-3.5 text-teal-400 inline shrink-0' },
  '⏱️': { icon: Clock, className: 'w-3.5 h-3.5 text-slate-400 inline shrink-0' },
  '⏱': { icon: Clock, className: 'w-3.5 h-3.5 text-slate-400 inline shrink-0' },
  '⏰': { icon: Clock, className: 'w-3.5 h-3.5 text-slate-400 inline shrink-0' },
  '📱': { icon: Smartphone, className: 'w-3.5 h-3.5 text-slate-400 inline shrink-0' },
  '🌐': { icon: Globe, className: 'w-3.5 h-3.5 text-sky-400 inline shrink-0' },
  '🔗': { icon: Link, className: 'w-3.5 h-3.5 text-indigo-400 inline shrink-0' },
  '🎯': { icon: Target, className: 'w-3.5 h-3.5 text-rose-400 inline shrink-0' },
  '🛡️': { icon: Shield, className: 'w-3.5 h-3.5 text-emerald-400 inline shrink-0' },
  '🛡': { icon: Shield, className: 'w-3.5 h-3.5 text-emerald-400 inline shrink-0' },
  '🔌': { icon: Plug, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '📸': { icon: Camera, className: 'w-3.5 h-3.5 text-indigo-400 inline shrink-0' },
  '💤': { icon: Moon, className: 'w-3.5 h-3.5 text-slate-400 inline shrink-0' },
  '🛒': { icon: ShoppingCart, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '🎲': { icon: Dices, className: 'w-3.5 h-3.5 text-purple-400 inline shrink-0' },
  '⏳': { icon: Hourglass, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '⌛': { icon: Hourglass, className: 'w-3.5 h-3.5 text-amber-400 inline shrink-0' },
  '📁': { icon: Folder, className: 'w-3.5 h-3.5 text-blue-400 inline shrink-0' },
  '🔴': { icon: Circle, className: 'w-2.5 h-2.5 text-rose-500 fill-rose-500 inline shrink-0' },
  '🟢': { icon: Circle, className: 'w-2.5 h-2.5 text-emerald-500 fill-emerald-500 inline shrink-0' },
  '🟡': { icon: Circle, className: 'w-2.5 h-2.5 text-amber-500 fill-amber-500 inline shrink-0' },
  '⚪': { icon: Circle, className: 'w-2.5 h-2.5 text-slate-400 fill-slate-400 inline shrink-0' },
};

// Regex matching all mapped emojis
const EMOJI_KEYS = Object.keys(EMOJI_ICON_MAP).sort((a, b) => b.length - a.length);
const EMOJI_REGEX = new RegExp(`(${EMOJI_KEYS.map((k) => k.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')).join('|')})`, 'g');

/**
 * Strips raw emojis and renders them as modern Lucide SVG React icons.
 */
export const FormattedTextWithIcons: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;

  const parts = text.split(EMOJI_REGEX);

  return (
    <span className="inline-flex items-center flex-wrap gap-x-1">
      {parts.map((part, index) => {
        const iconConf = EMOJI_ICON_MAP[part];
        if (iconConf) {
          const IconComponent = iconConf.icon;
          return <IconComponent key={index} className={iconConf.className} />;
        }
        return <React.Fragment key={index}>{part}</React.Fragment>;
      })}
    </span>
  );
};

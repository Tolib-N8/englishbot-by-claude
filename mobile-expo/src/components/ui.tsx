import {
  Pressable,
  Text,
  View,
  type PressableProps,
  type TextProps,
  type ViewProps,
  useColorScheme,
} from 'react-native';

export function useTokens() {
  const scheme = useColorScheme();
  const dark = scheme === 'dark';
  return {
    dark,
    bg: dark ? '#0B1220' : '#FAFAFA',
    surface: dark ? '#101827' : '#FFFFFF',
    surfaceAlt: dark ? '#1F2937' : '#F3F4F6',
    border: dark ? '#1F2937' : '#E5E7EB',
    text: dark ? '#F3F4F6' : '#111827',
    muted: dark ? '#94A3B8' : '#6B7280',
    primary: dark ? '#60A5FA' : '#2563EB',
    primaryFg: '#FFFFFF',
    success: '#16A34A',
    danger: '#DC2626',
    warn: '#D97706',
  };
}

export function Card({ children, style, ...rest }: ViewProps) {
  const t = useTokens();
  return (
    <View
      {...rest}
      style={[
        {
          backgroundColor: t.surface,
          borderColor: t.border,
          borderWidth: 1,
          borderRadius: 12,
          padding: 14,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

type ButtonProps = PressableProps & {
  variant?: 'primary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md';
  title: string;
};
export function Button({ variant = 'primary', size = 'md', title, style, disabled, ...rest }: ButtonProps) {
  const t = useTokens();
  const bg =
    variant === 'primary' ? t.primary :
    variant === 'danger' ? t.danger :
    'transparent';
  const fg =
    variant === 'primary' || variant === 'danger' ? t.primaryFg :
    t.text;
  const border = variant === 'outline' ? t.border : 'transparent';
  const py = size === 'sm' ? 6 : 10;
  const px = size === 'sm' ? 10 : 14;
  return (
    <Pressable
      {...rest}
      disabled={disabled}
      style={(state) => [
        {
          backgroundColor: bg,
          borderColor: border,
          borderWidth: variant === 'outline' ? 1 : 0,
          paddingVertical: py,
          paddingHorizontal: px,
          borderRadius: 8,
          opacity: disabled ? 0.5 : state.pressed ? 0.85 : 1,
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'row',
        },
        typeof style === 'function' ? style(state) : style,
      ]}
    >
      <Text style={{ color: fg, fontWeight: '600', fontSize: size === 'sm' ? 13 : 15 }}>{title}</Text>
    </Pressable>
  );
}

export function Heading({ children, style, ...rest }: TextProps) {
  const t = useTokens();
  return (
    <Text {...rest} style={[{ color: t.text, fontSize: 22, fontWeight: '700' }, style]}>
      {children}
    </Text>
  );
}

export function Subtle({ children, style, ...rest }: TextProps) {
  const t = useTokens();
  return (
    <Text {...rest} style={[{ color: t.muted, fontSize: 12 }, style]}>
      {children}
    </Text>
  );
}

export function Body({ children, style, ...rest }: TextProps) {
  const t = useTokens();
  return (
    <Text {...rest} style={[{ color: t.text, fontSize: 14 }, style]}>
      {children}
    </Text>
  );
}

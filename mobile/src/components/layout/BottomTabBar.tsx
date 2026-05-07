import React from 'react';
import { View, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { Badge } from '../primitives/Badge';

interface TabItem {
  key: string;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  activeIcon: keyof typeof Ionicons.glyphMap;
  badge?: number;
}

export interface BottomTabBarProps {
  activeTab: string;
  onTabPress: (key: string) => void;
  notificationCount?: number;
}

const tabs: TabItem[] = [
  {
    key: 'home',
    label: 'Home',
    icon: 'home-outline',
    activeIcon: 'home',
  },
  {
    key: 'profile',
    label: 'Profile',
    icon: 'person-outline',
    activeIcon: 'person',
  },
  {
    key: 'notifications',
    label: 'Alerts',
    icon: 'notifications-outline',
    activeIcon: 'notifications',
  },
];

export function BottomTabBar({
  activeTab,
  onTabPress,
  notificationCount = 0,
}: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <View
      style={[
        styles.container,
        { paddingBottom: Math.max(insets.bottom, tokens.spacing.sm) },
      ]}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;
        const iconName = isActive ? tab.activeIcon : tab.icon;
        const color = isActive
          ? tokens.color.accent.primary
          : tokens.color.text.muted;
        const showBadge = tab.key === 'notifications' && notificationCount > 0;

        return (
          <Pressable
            key={tab.key}
            onPress={() => onTabPress(tab.key)}
            style={styles.tab}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
            accessibilityLabel={tab.label}
          >
            <View style={styles.iconContainer}>
              <Ionicons
                name={iconName}
                size={tokens.size.iconStandard}
                color={color}
              />
              {showBadge && (
                <View style={styles.badgeContainer}>
                  <View style={styles.badgeDot}>
                    <Text
                      variant="captionBold"
                      color="white"
                      style={styles.badgeText}
                    >
                      {notificationCount > 99 ? '99+' : String(notificationCount)}
                    </Text>
                  </View>
                </View>
              )}
            </View>
            <Text
              variant="captionBold"
              style={{ color, marginTop: tokens.spacing.xs / 2 }}
            >
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: tokens.color.bg.elevated,
    borderTopWidth: 1,
    borderTopColor: tokens.color.border.subtle,
    paddingTop: tokens.spacing.sm,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: tokens.size.touchTarget,
  },
  iconContainer: {
    position: 'relative',
  },
  badgeContainer: {
    position: 'absolute',
    top: -tokens.spacing.xs,
    right: -tokens.spacing.sm,
  },
  badgeDot: {
    backgroundColor: tokens.color.semantic.negative,
    borderRadius: tokens.spacing.sm,
    minWidth: tokens.spacing.base,
    height: tokens.spacing.base,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: tokens.spacing.xs,
  },
  badgeText: {
    fontSize: 10,
    lineHeight: 12,
  },
});

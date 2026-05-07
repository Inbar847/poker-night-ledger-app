import React, { useEffect, useRef } from 'react';
import { View, Animated, StyleSheet, ViewStyle, DimensionValue, AccessibilityInfo } from 'react-native';
import { tokens } from '@/theme';

export interface SkeletonProps {
  width?: DimensionValue;
  height?: number;
  radius?: number;
  circle?: boolean;
  style?: ViewStyle;
}

export function Skeleton({
  width = '100%',
  height = 20,
  radius = tokens.radius.md,
  circle = false,
  style,
}: SkeletonProps) {
  const shimmer = useRef(new Animated.Value(0)).current;
  const reducedMotion = useRef(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      reducedMotion.current = enabled;
    });
  }, []);

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    );

    if (!reducedMotion.current) {
      animation.start();
    }

    return () => animation.stop();
  }, [shimmer]);

  const opacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.6],
  });

  const resolvedRadius = circle ? (typeof height === 'number' ? height / 2 : radius) : radius;

  return (
    <Animated.View
      style={[
        styles.base,
        {
          width: circle ? height : width,
          height,
          borderRadius: resolvedRadius,
          opacity: reducedMotion.current ? 0.4 : opacity,
        },
        style,
      ]}
      accessibilityLabel="Loading"
    />
  );
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: tokens.color.bg.surface,
  },
});

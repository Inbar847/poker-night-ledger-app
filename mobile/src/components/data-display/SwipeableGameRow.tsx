import React, { useCallback, useRef } from 'react';
import { Animated, Pressable, StyleSheet, View } from 'react-native';
import Swipeable from 'react-native-gesture-handler/Swipeable';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';

const ACTION_WIDTH = 90;

interface SwipeableGameRowProps {
  children: React.ReactNode;
  onHide: () => void;
  disabled?: boolean;
}

export function SwipeableGameRow({
  children,
  onHide,
  disabled = false,
}: SwipeableGameRowProps) {
  const swipeableRef = useRef<Swipeable>(null);

  const handleHide = useCallback(() => {
    swipeableRef.current?.close();
    onHide();
  }, [onHide]);

  const renderRightActions = useCallback(
    (
      _progress: Animated.AnimatedInterpolation<number>,
      dragX: Animated.AnimatedInterpolation<number>,
    ) => {
      const scale = dragX.interpolate({
        inputRange: [-ACTION_WIDTH, 0],
        outputRange: [1, 0.5],
        extrapolate: 'clamp',
      });

      return (
        <Pressable style={styles.actionContainer} onPress={handleHide}>
          <Animated.View style={{ transform: [{ scale }] }}>
            <Text variant="captionBold" style={styles.actionText}>
              Hide
            </Text>
          </Animated.View>
        </Pressable>
      );
    },
    [handleHide],
  );

  if (disabled) {
    return <>{children}</>;
  }

  return (
    <Swipeable
      ref={swipeableRef}
      renderRightActions={renderRightActions}
      rightThreshold={40}
      friction={2}
      overshootRight={false}
    >
      <View style={styles.content}>{children}</View>
    </Swipeable>
  );
}

const styles = StyleSheet.create({
  actionContainer: {
    width: ACTION_WIDTH,
    backgroundColor: tokens.color.semantic.negative,
    justifyContent: 'center',
    alignItems: 'center',
    borderTopRightRadius: tokens.radius.lg,
    borderBottomRightRadius: tokens.radius.lg,
  },
  content: {
    backgroundColor: tokens.color.bg.primary,
  },
  actionText: {
    color: tokens.color.white,
  },
});

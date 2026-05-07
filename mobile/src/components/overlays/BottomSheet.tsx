import React, { useEffect, useRef } from 'react';
import {
  View,
  Pressable,
  Animated,
  StyleSheet,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { tokens } from '@/theme';
import { shadows } from '@/theme';
import { Text } from '../primitives/Text';
import { Divider } from '../primitives/Divider';

type SheetHeight = 'auto' | '50%' | '60%' | '80%';

export interface BottomSheetProps {
  visible: boolean;
  onDismiss: () => void;
  title?: string;
  height?: SheetHeight;
  preventDismiss?: boolean;
  children: React.ReactNode;
}

const { height: screenHeight } = Dimensions.get('window');

const heightMap: Record<SheetHeight, number | undefined> = {
  auto: undefined,
  '50%': screenHeight * 0.5,
  '60%': screenHeight * 0.6,
  '80%': screenHeight * 0.8,
};

export function BottomSheet({
  visible,
  onDismiss,
  title,
  height = 'auto',
  preventDismiss = false,
  children,
}: BottomSheetProps) {
  const translateY = useRef(new Animated.Value(screenHeight)).current;
  const backdropOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: 0,
          duration: 250,
          useNativeDriver: true,
        }),
        Animated.timing(backdropOpacity, {
          toValue: 1,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(translateY, {
          toValue: screenHeight,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(backdropOpacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, translateY, backdropOpacity]);

  if (!visible) return null;

  const sheetHeight = heightMap[height];

  return (
    <View style={styles.overlay}>
      <Animated.View style={[styles.backdrop, { opacity: backdropOpacity }]}>
        <Pressable
          style={styles.backdropPress}
          onPress={preventDismiss ? undefined : onDismiss}
        />
      </Animated.View>
      <Animated.View
        style={[
          styles.sheet,
          shadows.elevated,
          { transform: [{ translateY }] },
          sheetHeight ? { height: sheetHeight } : undefined,
        ]}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.flex}
        >
          <View style={styles.dragHandleContainer}>
            <View style={styles.dragHandle} />
          </View>
          {title && (
            <>
              <View style={styles.titleContainer}>
                <Text variant="h3">{title}</Text>
              </View>
              <Divider subtle />
            </>
          )}
          <View style={styles.content}>{children}</View>
        </KeyboardAvoidingView>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'flex-end',
    zIndex: 1000,
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  backdropPress: {
    flex: 1,
  },
  sheet: {
    backgroundColor: tokens.color.bg.elevated,
    borderTopLeftRadius: tokens.radius.xl,
    borderTopRightRadius: tokens.radius.xl,
    maxHeight: screenHeight * 0.8,
  },
  flex: {
    flex: 1,
  },
  dragHandleContainer: {
    alignItems: 'center',
    paddingTop: tokens.spacing.sm,
    paddingBottom: tokens.spacing.xs,
  },
  dragHandle: {
    width: tokens.size.dragHandleWidth,
    height: tokens.size.dragHandleHeight,
    borderRadius: tokens.size.dragHandleHeight / 2,
    backgroundColor: tokens.color.border.default,
  },
  titleContainer: {
    paddingHorizontal: tokens.spacing.lg,
    paddingVertical: tokens.spacing.md,
  },
  content: {
    paddingHorizontal: tokens.spacing.lg,
    paddingVertical: tokens.spacing.base,
    flexGrow: 1,
  },
});

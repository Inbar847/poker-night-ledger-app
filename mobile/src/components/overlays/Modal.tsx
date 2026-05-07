import React, { useEffect, useRef } from 'react';
import { View, Pressable, Animated, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { shadows } from '@/theme';

export interface ModalProps {
  visible: boolean;
  onDismiss?: () => void;
  children: React.ReactNode;
}

export function Modal({ visible, onDismiss, children }: ModalProps) {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(opacity, {
      toValue: visible ? 1 : 0,
      duration: 200,
      useNativeDriver: true,
    }).start();
  }, [visible, opacity]);

  if (!visible) return null;

  return (
    <View style={styles.overlay}>
      <Animated.View style={[styles.backdrop, { opacity }]}>
        <Pressable style={styles.backdropPress} onPress={onDismiss} />
      </Animated.View>
      <Animated.View
        style={[
          styles.modal,
          shadows.elevated,
          { opacity },
        ]}
      >
        {children}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  backdropPress: {
    flex: 1,
  },
  modal: {
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.xl,
    padding: tokens.spacing.xl,
    marginHorizontal: tokens.spacing['2xl'],
    maxWidth: 360,
    width: '100%',
  },
});

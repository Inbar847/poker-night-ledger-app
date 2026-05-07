import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { Button } from '../primitives/Button';
import { Spacer } from '../primitives/Spacer';
import { Modal } from './Modal';

export interface ConfirmDialogProps {
  visible: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  confirmVariant?: 'primary' | 'destructive';
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  visible,
  title,
  message,
  confirmLabel = 'Confirm',
  confirmVariant = 'destructive',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal visible={visible} onDismiss={onCancel}>
      <Text variant="h3" align="center">
        {title}
      </Text>
      <Spacer size="sm" />
      <Text variant="body" color="secondary" align="center">
        {message}
      </Text>
      <Spacer size="xl" />
      <View style={styles.actions}>
        <View style={styles.buttonWrapper}>
          <Button
            label={cancelLabel}
            variant="secondary"
            onPress={onCancel}
            fullWidth
          />
        </View>
        <View style={styles.buttonWrapper}>
          <Button
            label={confirmLabel}
            variant={confirmVariant}
            onPress={onConfirm}
            fullWidth
          />
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  actions: {
    flexDirection: 'row',
    gap: tokens.spacing.md,
  },
  buttonWrapper: {
    flex: 1,
  },
});

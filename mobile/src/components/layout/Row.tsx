import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { tokens } from '@/theme';

type RowAlign = 'start' | 'center' | 'end' | 'stretch';
type RowJustify = 'start' | 'center' | 'end' | 'between' | 'around';

const alignMap: Record<RowAlign, ViewStyle['alignItems']> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  stretch: 'stretch',
};

const justifyMap: Record<RowJustify, ViewStyle['justifyContent']> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  between: 'space-between',
  around: 'space-around',
};

export interface RowProps {
  align?: RowAlign;
  justify?: RowJustify;
  gap?: keyof typeof tokens.spacing;
  wrap?: boolean;
  style?: ViewStyle;
  children: React.ReactNode;
}

export function Row({
  align = 'center',
  justify = 'start',
  gap,
  wrap = false,
  style,
  children,
}: RowProps) {
  return (
    <View
      style={[
        styles.row,
        {
          alignItems: alignMap[align],
          justifyContent: justifyMap[justify],
          gap: gap ? tokens.spacing[gap] : undefined,
          flexWrap: wrap ? 'wrap' : 'nowrap',
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
  },
});

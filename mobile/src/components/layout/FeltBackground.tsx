/**
 * FeltBackground — matte poker-table felt surface.
 *
 * The material feel comes from TEXTURE, not gradients. Smooth gradients
 * read as polished/digital surfaces no matter how subtle. Real poker felt
 * reads as fabric because of dense, directional fiber grain visible at
 * arm's-length.
 *
 * Texture strategy: the same small noise tile is rendered multiple times
 * with different scale transforms:
 *
 *  - Stretched horizontally (scaleX ~3): each noise speckle becomes an
 *    elongated horizontal mark → reads as pressed fiber running across
 *    the table surface. This is the dominant texture.
 *
 *  - Normal scale: micro-grain of the felt weave. Adds matte, dry,
 *    non-reflective surface quality.
 *
 *  - Stretched vertically (scaleY ~2): cross-fiber hints. Much fainter.
 *    Prevents the texture from being purely one-directional.
 *
 *  - Slight rotation (~3°): breaks tile repetition. Adds organic
 *    irregularity so it feels like real material, not a digital pattern.
 *
 * Gradients are minimal — just enough ambient depth for the felt to
 * feel like it sits on a table (slightly darker edges/bottom), not
 * enough to create any polished-surface sheen.
 */

import { LinearGradient } from 'expo-linear-gradient';
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';

import { tokens } from '@/theme';

// ---------------------------------------------------------------------------
// Noise tile — 8×8 pixel PNG with alpha-only speckles.
// The same tile is reused at multiple scales/rotations to build up the
// layered felt texture.
// ---------------------------------------------------------------------------

const GRAIN_URI =
  'data:image/png;base64,' +
  'iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAAXNSR0IArs4c6QAA' +
  'AERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAACKADAAQAAAABAAAACAAAAACm' +
  'oJqJAAAARklEQVQYGWN0dff5z8DAwMgABUwMUAAi' +
  'GBnQ5BgZkKWQhJC1MLJgkcfQgsONoIYR1RUMrHgdwICuEsOIRTFAAz0KGBkBAPcdFb1bSHjpAAAAAElFTkSuQmCC';

export interface FeltBackgroundProps {
  children?: React.ReactNode;
}

export function FeltBackground({ children }: FeltBackgroundProps) {
  const { felt, bg } = tokens.color;

  return (
    <View style={[styles.root, { backgroundColor: bg.primary }]}>

      {/* ── Ambient depth ── */}
      {/* Very flat gradient: just enough to feel like a table surface
          under even room lighting, not enough to create any sheen. */}
      <LinearGradient
        colors={[felt.highlight, bg.primary, bg.primary, felt.shadow]}
        locations={[0, 0.25, 0.7, 1]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      />

      {/* ── Edge shadows (table rails) ── */}
      <LinearGradient
        colors={[`${felt.shadow}38`, 'transparent']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0.5 }}
        end={{ x: 0.25, y: 0.5 }}
      />
      <LinearGradient
        colors={['transparent', `${felt.shadow}38`]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.75, y: 0.5 }}
        end={{ x: 1, y: 0.5 }}
      />
      <LinearGradient
        colors={['transparent', `${felt.shadow}28`]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.5, y: 0.8 }}
        end={{ x: 0.5, y: 1 }}
      />

      {/* ── FIBER TEXTURE (dominant layer) ──
          Noise tile stretched 3× horizontally: each random dot becomes a
          short horizontal fiber strand. This is what makes the surface
          read as compressed textile. */}
      <View style={styles.textureClip} pointerEvents="none">
        <Image
          source={{ uri: GRAIN_URI }}
          style={[StyleSheet.absoluteFill, styles.fiberHorizontal]}
          resizeMode="repeat"
        />
      </View>

      {/* ── CROSS-FIBER (secondary) ──
          Same tile stretched vertically: faint perpendicular fiber hints
          that add woven-textile depth without fighting the dominant
          horizontal direction. */}
      <View style={styles.textureClip} pointerEvents="none">
        <Image
          source={{ uri: GRAIN_URI }}
          style={[StyleSheet.absoluteFill, styles.fiberCross]}
          resizeMode="repeat"
        />
      </View>

      {/* ── MICRO-GRAIN (matte surface) ──
          Tile at native scale: the fine random noise that makes the
          surface read as dry/matte rather than smooth/reflective. */}
      <View
        style={[StyleSheet.absoluteFill, styles.grainMicro]}
        pointerEvents="none"
      >
        <Image
          source={{ uri: GRAIN_URI }}
          style={StyleSheet.absoluteFill}
          resizeMode="repeat"
        />
      </View>

      {/* ── ORGANIC BREAK ──
          Tile rotated ~3°: the slight angle means its repeat grid doesn't
          align with the other layers, breaking up any visible tiling
          pattern and adding natural irregularity. */}
      <View style={styles.textureClip} pointerEvents="none">
        <Image
          source={{ uri: GRAIN_URI }}
          style={[StyleSheet.absoluteFill, styles.grainRotated]}
          resizeMode="repeat"
        />
      </View>

      {/* ── DYE IRREGULARITY ──
          Very faint warm-cool drift so the color isn't digitally uniform. */}
      <LinearGradient
        colors={['transparent', '#14332B05', '#18372F04', 'transparent']}
        locations={[0, 0.35, 0.6, 0.9]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.25, y: 0.2 }}
        end={{ x: 0.75, y: 0.85 }}
      />

      {/* Content above all layers */}
      <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    overflow: 'hidden',
  },

  /** Clips transformed texture layers that extend beyond the root bounds */
  textureClip: {
    ...StyleSheet.absoluteFillObject,
    overflow: 'hidden',
  },

  /** Horizontal fiber: stretched 3× wide, each noise dot ≈ 24×8 → short fiber strands */
  fiberHorizontal: {
    opacity: 0.14,
    transform: [{ scaleX: 3 }],
  },

  /** Cross-fiber: stretched 2× tall, faint perpendicular weave hint */
  fiberCross: {
    opacity: 0.05,
    transform: [{ scaleY: 2 }],
  },

  /** Micro-grain at native 8×8 scale: matte surface finish */
  grainMicro: {
    opacity: 0.09,
  },

  /** Rotated grain: breaks tile alignment for organic irregularity */
  grainRotated: {
    opacity: 0.04,
    transform: [{ rotate: '3deg' }, { scale: 1.06 }],
  },
});

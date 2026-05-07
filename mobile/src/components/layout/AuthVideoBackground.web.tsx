/**
 * AuthVideoBackground — web-specific implementation.
 *
 * Metro/Expo automatically picks this file over `AuthVideoBackground.tsx` when
 * bundling for `platform=web`. Native (iOS/Android) keeps using the original
 * `expo-video` implementation untouched.
 *
 * Why a separate web file:
 *  - `expo-video`'s `VideoView` wraps the underlying <video> in a container that
 *    does not honour `StyleSheet.absoluteFill` reliably on web — the video
 *    rendered at intrinsic size in the corner.
 *  - Browser autoplay policy requires `muted` + `playsInline` to be present on
 *    the <video> tag *before* the source loads. Going through expo-video
 *    sometimes lost autoplay because muted was applied after load.
 *
 * Layers (bottom to top):
 *  1. Felt-green fallback fill.
 *  2. Looping muted HTML <video> covering the viewport (object-fit: cover).
 *  3. Dark overlay gradient.
 *  4. Children (auth screen content).
 */

import { LinearGradient } from 'expo-linear-gradient';
import React from 'react';
import { Image, StyleSheet, View } from 'react-native';

import { tokens } from '@/theme';

// `Image.resolveAssetSource` resolves the bundler-specific asset reference into
// a string URL that survives `expo export --platform web` (the asset is hashed
// and copied to dist/assets/...).
const VIDEO_SRC =
  Image.resolveAssetSource(
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('../../../assets/videos/auth-welcome.mp4'),
  )?.uri ?? '';

export interface AuthVideoBackgroundProps {
  /** Overlay darkness — 0 (no overlay) to 1 (black). Default 0.55 */
  overlayOpacity?: number;
  children?: React.ReactNode;
}

export function AuthVideoBackground({
  overlayOpacity = 0.55,
  children,
}: AuthVideoBackgroundProps) {
  const overlayTop = `rgba(0,0,0,${(overlayOpacity * 0.6).toFixed(2)})`;
  const overlayMid = `rgba(0,0,0,${overlayOpacity.toFixed(2)})`;
  const overlayBot = `rgba(10,44,35,${Math.min(overlayOpacity + 0.2, 0.85).toFixed(2)})`;

  return (
    <View style={styles.root}>
      {/* Layer 1 — fallback fill (visible if the video fails to load) */}
      <View
        style={[
          StyleSheet.absoluteFill,
          { backgroundColor: tokens.color.bg.primary },
        ]}
      />

      {/* Layer 2 — HTML <video>. Raw DOM element so the browser autoplay
          policy gets exactly what it expects (muted + playsInline + no
          controls). `pointer-events: none` keeps clicks reaching the form. */}
      {VIDEO_SRC ? (
        <video
          src={VIDEO_SRC}
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          aria-hidden
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            zIndex: 0,
            pointerEvents: 'none',
          }}
        />
      ) : null}

      {/* Layer 3 — dark overlay gradient for text legibility */}
      <LinearGradient
        colors={[overlayTop, overlayMid, overlayBot]}
        locations={[0, 0.5, 1]}
        style={[StyleSheet.absoluteFill, webZ(1)]}
        pointerEvents="none"
      />

      {/* Layer 4 — children (form, brand hero, etc.) */}
      <View
        style={[StyleSheet.absoluteFill, webZ(2)]}
        pointerEvents="box-none"
      >
        {children}
      </View>
    </View>
  );
}

// React Native's StyleSheet doesn't include zIndex inside absoluteFill; we layer
// explicitly on web so the overlay sits above the video and content above both.
function webZ(zIndex: number) {
  return { zIndex } as const;
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    minHeight: '100%',
    width: '100%',
    backgroundColor: tokens.color.bg.primary,
    overflow: 'hidden',
    position: 'relative',
  },
});

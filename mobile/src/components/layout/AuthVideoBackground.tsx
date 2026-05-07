/**
 * AuthVideoBackground — cinematic full-screen video backdrop for auth screens.
 *
 * Layers (bottom to top):
 *  1. Felt-green fallback fill (visible if video hasn't loaded or is missing)
 *  2. Looping muted video covering the full screen
 *  3. Dark overlay gradient for text/form legibility
 *  4. Children (auth screen content)
 *
 * The video file is expected at: assets/videos/auth-welcome.mp4
 * If the file is missing the component gracefully falls back to FeltBackground.
 *
 * To activate the video background:
 *  1. Drop an .mp4 file at mobile/assets/videos/auth-welcome.mp4
 *  2. Uncomment the VIDEO_SOURCE line below
 *  3. Rebuild (Metro needs to re-bundle the asset)
 *
 * Usage:
 *   <AuthVideoBackground>
 *     <YourAuthContent />
 *   </AuthVideoBackground>
 */

import { LinearGradient } from 'expo-linear-gradient';
import { useVideoPlayer, VideoView } from 'expo-video';
import type { VideoSource } from 'expo-video';
import React, { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { tokens } from '@/theme';
import { FeltBackground } from './FeltBackground';

// ---------------------------------------------------------------------------
// Video source
//
// Uncomment the line below once the video asset exists at the expected path.
// Metro bundler requires the file to exist at bundle time — a require() for
// a missing file will fail the build, so we keep it commented until the
// asset is in place.
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-require-imports
const VIDEO_ASSET: VideoSource = require('../../../assets/videos/auth-welcome.mp4');

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface AuthVideoBackgroundProps {
  /** Overlay darkness — 0 (no overlay) to 1 (black). Default 0.55 */
  overlayOpacity?: number;
  children?: React.ReactNode;
}

export function AuthVideoBackground({
  overlayOpacity = 0.55,
  children,
}: AuthVideoBackgroundProps) {
  const [videoFailed, setVideoFailed] = useState(false);

  const player = useVideoPlayer(VIDEO_ASSET, (p) => {
    p.loop = true;
    p.muted = true;
    p.play();
  });

  // Listen for player errors and fall back gracefully.
  useEffect(() => {
    if (!VIDEO_ASSET) return;

    const sub = player.addListener('statusChange', (payload) => {
      if (payload.status === 'error') {
        setVideoFailed(true);
      }
    });
    return () => sub.remove();
  }, [player]);

  // No video source or player error → graceful felt background fallback
  if (!VIDEO_ASSET || videoFailed) {
    return <FeltBackground>{children}</FeltBackground>;
  }

  // Overlay color stops: deep felt-green at bottom for grounding,
  // semi-transparent black elsewhere for readability.
  const overlayTop = `rgba(0,0,0,${(overlayOpacity * 0.6).toFixed(2)})`;
  const overlayMid = `rgba(0,0,0,${overlayOpacity.toFixed(2)})`;
  const overlayBot = `rgba(10,44,35,${Math.min(overlayOpacity + 0.2, 0.85).toFixed(2)})`;

  return (
    <View style={styles.root}>
      {/* Layer 1 — fallback fill (visible before video loads) */}
      <View
        style={[StyleSheet.absoluteFill, { backgroundColor: tokens.color.bg.primary }]}
      />

      {/* Layer 2 — looping video */}
      <VideoView
        player={player}
        style={StyleSheet.absoluteFill}
        contentFit="cover"
        nativeControls={false}
        allowsFullscreen={false}
        allowsPictureInPicture={false}
      />

      {/* Layer 3 — dark overlay gradient */}
      <LinearGradient
        colors={[overlayTop, overlayMid, overlayBot]}
        locations={[0, 0.5, 1]}
        style={StyleSheet.absoluteFill}
      />

      {/* Layer 4 — content */}
      <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: tokens.color.bg.primary,
  },
});

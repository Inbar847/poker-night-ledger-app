/**
 * Profile screen — view and edit the current user's profile.
 *
 * View mode:    displays user data (name, email, phone, profile image).
 * Edit mode:    form with react-hook-form + zod for mutable fields.
 *               Profile image URL is a text input (no file picker in Stage 6).
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient, useMutation, useQuery } from "@tanstack/react-query";
import { Stack, useRouter } from "expo-router";
import { useState } from "react";
import { useForm } from "react-hook-form";
import {
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { z } from "zod";

import {
  Avatar,
  Badge,
  BottomTabBar,
  Button,
  Card,
  ConfirmDialog,
  Divider,
  EmptyState,
  ErrorState,
  FeltBackground,
  Input,
  Row,
  Section,
  Skeleton,
  Spacer,
  StatCard,
  Text,
  FormField,
  MoneyAmount,
} from "@/components";
import { useUnreadCount } from "@/hooks/useNotifications";
import { queryKeys } from "@/lib/queryKeys";
import * as statsService from "@/services/statsService";
import * as userService from "@/services/userService";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";
import type { UserStats } from "@/types/stats";
import type { User } from "@/types/user";

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const editSchema = z.object({
  full_name: z.string().min(1, "Name cannot be empty").optional().or(z.literal("")),
  phone: z.string().optional().or(z.literal("")),
  profile_image_url: z
    .string()
    .url("Must be a valid URL")
    .optional()
    .or(z.literal("")),
});

type EditValues = z.infer<typeof editSchema>;

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatsSection({ stats }: { stats: UserStats }) {
  const router = useRouter();
  const net = parseFloat(stats.cumulative_net);
  const avgNet = stats.average_net != null ? parseFloat(stats.average_net) : null;

  return (
    <Section
      title="My Stats"
      action={
        <Button
          label="History"
          variant="ghost"
          size="md"
          onPress={() => router.push("/history")}
        />
      }
    >
      {/* Hero net result card */}
      <Card variant="prominent" padding="comfortable">
        <View style={styles.netHero}>
          <Text variant="caption" color="secondary">Cumulative net</Text>
          <Spacer size="xs" />
          {stats.games_with_result > 0 ? (
            <MoneyAmount amount={net} size="lg" showSign />
          ) : (
            <Text variant="numericLarge" color="secondary">{"\u2014"}</Text>
          )}
        </View>
        {avgNet != null && (
          <>
            <Divider subtle spacing={tokens.spacing.sm} />
            <Row justify="between" align="center">
              <Text variant="caption" color="secondary">Avg per game</Text>
              <MoneyAmount amount={avgNet} size="sm" showSign />
            </Row>
          </>
        )}
      </Card>

      <Spacer size="base" />

      {/* Stats grid */}
      <View style={styles.statsGrid}>
        <View style={styles.statHalf}>
          <StatCard
            label="Games played"
            value={String(stats.total_games_played)}
          />
        </View>
        <View style={styles.statHalf}>
          <StatCard
            label="Games hosted"
            value={String(stats.total_games_hosted)}
          />
        </View>
        <View style={styles.statHalf}>
          <StatCard
            label="Profitable"
            value={String(stats.profitable_games)}
            valueColor="positive"
          />
        </View>
        <View style={styles.statHalf}>
          <StatCard
            label="Win rate"
            value={
              stats.win_rate != null
                ? `${(stats.win_rate * 100).toFixed(0)}%`
                : "\u2014"
            }
          />
        </View>
      </View>

      <Spacer size="base" />

      {/* Quick links */}
      <Row gap="md">
        <View style={styles.linkHalf}>
          <Button
            label="Friends"
            variant="secondary"
            fullWidth
            onPress={() => router.push("/friends")}
          />
        </View>
        <View style={styles.linkHalf}>
          <Button
            label="Leaderboard"
            variant="secondary"
            fullWidth
            onPress={() => router.push("/leaderboard")}
          />
        </View>
      </Row>
    </Section>
  );
}

function ProfileInfoCard({ label, value }: { label: string; value?: string | null }) {
  return (
    <Row justify="between" align="center" style={styles.profileRow}>
      <Text variant="captionBold" color="secondary">{label}</Text>
      <Text variant="body" numberOfLines={1} style={styles.profileRowValue}>
        {value || "\u2014"}
      </Text>
    </Row>
  );
}

function EditForm({
  user,
  userId,
  onCancel,
  onSaved,
}: {
  user: User;
  userId: string;
  onCancel: () => void;
  onSaved: () => void;
}) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: userService.updateMe,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.me(userId) });
      onSaved();
    },
  });

  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<EditValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      full_name: user.full_name ?? "",
      phone: user.phone ?? "",
      profile_image_url: user.profile_image_url ?? "",
    },
  });

  const fullName = watch("full_name");
  const phone = watch("phone");
  const imageUrl = watch("profile_image_url");

  const onSubmit = async (values: EditValues) => {
    await mutation.mutateAsync({
      full_name: values.full_name || null,
      phone: values.phone || null,
      profile_image_url: values.profile_image_url || null,
    });
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Section title="Edit Profile">
        {mutation.error ? (
          <>
            <Card variant="default" padding="compact" style={styles.errorBanner}>
              <Text variant="caption" color="negative">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : "Update failed"}
              </Text>
            </Card>
            <Spacer size="md" />
          </>
        ) : null}

        <FormField label="Full name" error={errors.full_name?.message}>
          <Input
            placeholder="Your name"
            value={fullName}
            onChangeText={(v: string) =>
              setValue("full_name", v, { shouldValidate: true })
            }
            error={errors.full_name?.message}
          />
        </FormField>

        <FormField label="Phone" error={errors.phone?.message}>
          <Input
            placeholder="+1 555 000 0000"
            keyboardType="phone-pad"
            value={phone}
            onChangeText={(v: string) => setValue("phone", v, { shouldValidate: true })}
            error={errors.phone?.message}
          />
        </FormField>

        <FormField label="Profile image URL" error={errors.profile_image_url?.message}>
          <Input
            placeholder="https://example.com/avatar.jpg"
            autoCapitalize="none"
            keyboardType="url"
            value={imageUrl}
            onChangeText={(v: string) =>
              setValue("profile_image_url", v, { shouldValidate: true })
            }
            error={errors.profile_image_url?.message}
          />
        </FormField>

        <Spacer size="base" />

        <Row gap="md">
          <View style={styles.actionHalf}>
            <Button
              label="Cancel"
              variant="secondary"
              fullWidth
              onPress={onCancel}
              disabled={mutation.isPending}
            />
          </View>
          <View style={styles.actionHalf}>
            <Button
              label="Save"
              variant="primary"
              fullWidth
              loading={mutation.isPending}
              disabled={mutation.isPending}
              onPress={handleSubmit(onSubmit)}
            />
          </View>
        </Row>
      </Section>
    </KeyboardAvoidingView>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function ProfileSkeleton() {
  return (
    <View>
      {/* Avatar hero */}
      <Card variant="prominent" padding="comfortable">
        <View style={styles.centered}>
          <Skeleton width={80} height={80} circle />
          <Spacer size="md" />
          <Skeleton width={160} height={22} />
          <Spacer size="sm" />
          <Skeleton width={200} height={14} />
        </View>
      </Card>
      <Spacer size="xl" />

      {/* Details card */}
      <Skeleton height={160} radius={tokens.radius.lg} />
      <Spacer size="xl" />

      {/* Stats */}
      <Skeleton width={100} height={18} />
      <Spacer size="md" />
      <Skeleton height={100} radius={tokens.radius.xl} />
      <Spacer size="base" />
      <View style={styles.statsGrid}>
        <View style={styles.statHalf}>
          <Skeleton height={80} radius={tokens.radius.lg} />
        </View>
        <View style={styles.statHalf}>
          <Skeleton height={80} radius={tokens.radius.lg} />
        </View>
        <View style={styles.statHalf}>
          <Skeleton height={80} radius={tokens.radius.lg} />
        </View>
        <View style={styles.statHalf}>
          <Skeleton height={80} radius={tokens.radius.lg} />
        </View>
      </View>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function ProfileScreen() {
  const [isEditing, setIsEditing] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const router = useRouter();
  const userId = useAuthStore((s) => s.userId) ?? "";
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const { data: user, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: queryKeys.me(userId),
    queryFn: userService.getMe,
  });

  const { data: stats } = useQuery({
    queryKey: queryKeys.stats(userId),
    queryFn: statsService.getStats,
  });

  const { data: unreadData } = useUnreadCount();
  const unreadCount = unreadData?.count ?? 0;
  const insets = useSafeAreaInsets();

  const handleTabPress = (key: string) => {
    if (key === "profile") return; // already here
    if (key === "home") router.push("/games");
    if (key === "notifications") router.push("/notifications");
  };

  const renderContent = () => {
    if (isLoading) {
      return <ProfileSkeleton />;
    }

    if (error || !user) {
      return (
        <ErrorState
          message="Failed to load profile"
          onRetry={() => void refetch()}
        />
      );
    }

    return (
      <>
        {/* Avatar & Identity hero */}
        <Card variant="prominent" padding="comfortable">
          <View style={styles.centered}>
            <Avatar
              uri={user.profile_image_url}
              name={user.full_name ?? user.email}
              size="lg"
            />
            <Spacer size="md" />
            <Text variant="h2" align="center">{user.full_name ?? "\u2014"}</Text>
            <Spacer size="xs" />
            <Text variant="caption" color="secondary" align="center">
              {user.email}
            </Text>
          </View>
        </Card>

        <Spacer size="xl" />

        {isEditing ? (
          <EditForm
            user={user}
            userId={userId}
            onCancel={() => setIsEditing(false)}
            onSaved={() => setIsEditing(false)}
          />
        ) : (
          <>
            {/* Profile Details Card */}
            <Section title="Details">
              <Card variant="default" padding="comfortable">
                <ProfileInfoCard label="Email" value={user.email} />
                <Divider subtle spacing={tokens.spacing.sm} />
                <ProfileInfoCard label="Full name" value={user.full_name} />
                <Divider subtle spacing={tokens.spacing.sm} />
                <ProfileInfoCard label="Phone" value={user.phone} />
                <Divider subtle spacing={tokens.spacing.sm} />
                <ProfileInfoCard label="Image URL" value={user.profile_image_url} />
              </Card>
            </Section>

            {/* Stats */}
            {stats ? <StatsSection stats={stats} /> : null}

            {/* Actions */}
            <Section>
              <Button
                label="Edit Profile"
                variant="primary"
                fullWidth
                onPress={() => setIsEditing(true)}
              />
              <Spacer size="md" />
              <Button
                label="Log Out"
                variant="destructive"
                fullWidth
                onPress={() => setShowLogoutConfirm(true)}
              />
            </Section>
          </>
        )}
      </>
    );
  };

  return (
    <FeltBackground>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={styles.main}>
        <ScrollView
          style={styles.flex}
          contentContainerStyle={[
            styles.scrollContent,
            { paddingTop: insets.top + tokens.spacing.base },
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          refreshControl={
            !isEditing ? (
              <RefreshControl
                refreshing={isRefetching}
                onRefresh={refetch}
                tintColor={tokens.color.accent.primary}
                progressViewOffset={insets.top}
              />
            ) : undefined
          }
        >
          <View style={styles.headerRow}>
            <Text variant="h1">Profile</Text>
          </View>
          {renderContent()}
          <Spacer size="4xl" />
        </ScrollView>
      </View>

      <BottomTabBar
        activeTab="profile"
        onTabPress={handleTabPress}
        notificationCount={unreadCount}
      />

      <ConfirmDialog
        visible={showLogoutConfirm}
        title="Log Out"
        message="Are you sure you want to log out?"
        confirmLabel="Log Out"
        confirmVariant="destructive"
        onCancel={() => setShowLogoutConfirm(false)}
        onConfirm={async () => {
          setShowLogoutConfirm(false);
          await clearAuth();
        }}
      />
    </FeltBackground>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  flex: {
    flex: 1,
  },
  main: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: tokens.spacing.lg,
    paddingBottom: tokens.spacing["4xl"],
  },
  headerRow: {
    paddingBottom: tokens.spacing.lg,
  },
  centered: {
    alignItems: "center",
  },
  netHero: {
    alignItems: "center",
    paddingVertical: tokens.spacing.sm,
  },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: tokens.spacing.md,
  },
  statHalf: {
    width: "47%",
    flexGrow: 1,
  },
  linkHalf: {
    flex: 1,
  },
  actionHalf: {
    flex: 1,
  },
  profileRow: {
    paddingVertical: tokens.spacing.sm,
  },
  profileRowValue: {
    flex: 1,
    textAlign: "right",
    marginLeft: tokens.spacing.base,
  },
  errorBanner: {
    borderWidth: 1,
    borderColor: tokens.color.semantic.negative,
  },
});

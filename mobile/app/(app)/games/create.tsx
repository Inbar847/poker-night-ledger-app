/**
 * Create game screen.
 *
 * Fields: title (required), chip_cash_rate (required, > 0),
 *         currency (optional, default ILS).
 *
 * On success: navigate to the new game's screen.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Stack, useRouter } from "expo-router";
import { useForm } from "react-hook-form";
import { StyleSheet, View } from "react-native";
import { z } from "zod";

import {
  Text,
  Button,
  Input,
  Spacer,
  Screen,
  FormField,
  Card,
} from "@/components";
import { tokens } from "@/theme";
import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import { useAuthStore } from "@/store/authStore";

const schema = z.object({
  title: z.string().min(1, "Game title is required").max(255),
  chip_cash_rate: z
    .string()
    .min(1, "Chip/cash rate is required")
    .refine((v) => parseFloat(v) > 0, "Rate must be greater than 0"),
  currency: z.string().max(10).default("ILS"),
});

type FormValues = z.infer<typeof schema>;

export default function CreateGameScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const userId = useAuthStore((s) => s.userId) ?? "";

  const mutation = useMutation({
    mutationFn: gameService.createGame,
    onSuccess: (game) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.games(userId) });
      router.replace(`/games/${game.id}`);
    },
  });

  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: "", chip_cash_rate: "", currency: "ILS" },
  });

  const title = watch("title");
  const rate = watch("chip_cash_rate");
  const currency = watch("currency");

  const onSubmit = (values: FormValues) => {
    mutation.mutate({
      title: values.title,
      chip_cash_rate: values.chip_cash_rate,
      currency: values.currency || "ILS",
    });
  };

  return (
    <>
      <Stack.Screen options={{ title: "Create Game" }} />
      <Screen scrollable keyboardAvoiding>
        <View style={styles.content}>
          <Spacer size="base" />

          {mutation.error ? (
            <Card variant="default" padding="compact" style={styles.errorBanner}>
              <Text variant="caption" color="negative">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : "Failed to create game"}
              </Text>
            </Card>
          ) : null}

          <FormField label="Game title" error={errors.title?.message}>
            <Input
              placeholder="Friday Night Poker"
              value={title}
              onChangeText={(v) =>
                setValue("title", v, { shouldValidate: true })
              }
              error={errors.title?.message}
            />
          </FormField>

          <FormField
            label="Chip / cash rate"
            error={errors.chip_cash_rate?.message}
          >
            <Text variant="caption" color="muted" style={styles.hint}>
              How much cash (in {currency}) is one chip worth?
            </Text>
            <Spacer size="xs" />
            <Input
              placeholder="0.01"
              keyboardType="decimal-pad"
              value={rate}
              onChangeText={(v) =>
                setValue("chip_cash_rate", v, { shouldValidate: true })
              }
              error={errors.chip_cash_rate?.message}
            />
          </FormField>

          <FormField label="Currency">
            <Input
              placeholder="ILS"
              autoCapitalize="characters"
              maxLength={10}
              value={currency}
              onChangeText={(v) => setValue("currency", v.toUpperCase())}
            />
          </FormField>

          <Spacer size="xl" />

          <Button
            label="Create Game"
            variant="primary"
            size="lg"
            fullWidth
            loading={mutation.isPending}
            disabled={mutation.isPending}
            onPress={handleSubmit(onSubmit)}
          />

          <Spacer size="4xl" />
        </View>
      </Screen>
    </>
  );
}

const styles = StyleSheet.create({
  content: {
    paddingHorizontal: tokens.spacing.lg,
  },
  errorBanner: {
    backgroundColor: `${tokens.color.semantic.negative}1F`,
    borderWidth: 1,
    borderColor: `${tokens.color.semantic.negative}40`,
    marginBottom: tokens.spacing.base,
  },
  hint: {
    marginBottom: tokens.spacing.xs,
  },
});

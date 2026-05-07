/**
 * UserSearchInput — reusable debounced user search component.
 *
 * Calls /users/search as the user types (debounced 300ms).
 * Renders a selectable results list below the input.
 *
 * Search matches on full_name only (partial, case-insensitive). Email is not searchable.
 *
 * Usage:
 *   <UserSearchInput
 *     onSelect={(user) => handleUserSelected(user)}
 *     placeholder="Search by name…"
 *   />
 *
 * Used in: PublicProfileScreen (Stage 12), FriendsScreen (Stage 13),
 *          InviteFriendModal (Stage 22).
 */

import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { queryKeys } from "@/lib/queryKeys";
import { searchUsers } from "@/services/userService";
import { tokens } from "@/theme";
import type { UserSearchResult } from "@/types/user";

interface UserSearchInputProps {
  onSelect: (user: UserSearchResult) => void;
  placeholder?: string;
  /** Optionally clear the input after a user is selected (default true). */
  clearOnSelect?: boolean;
}

export default function UserSearchInput({
  onSelect,
  placeholder = "Search by name…",
  clearOnSelect = true,
}: UserSearchInputProps) {
  const [inputValue, setInputValue] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(inputValue.trim());
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [inputValue]);

  const { data: results = [], isFetching } = useQuery({
    queryKey: queryKeys.userSearch(debouncedQuery),
    queryFn: () => searchUsers(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    staleTime: 10_000,
  });

  const showResults = debouncedQuery.length >= 2;

  function handleSelect(user: UserSearchResult) {
    onSelect(user);
    if (clearOnSelect) {
      setInputValue("");
      setDebouncedQuery("");
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={inputValue}
          onChangeText={setInputValue}
          placeholder={placeholder}
          placeholderTextColor={tokens.color.text.muted}
          autoCapitalize="none"
          autoCorrect={false}
          returnKeyType="search"
        />
        {isFetching && <ActivityIndicator size="small" color={tokens.color.accent.primary} style={styles.spinner} />}
      </View>

      {showResults && results.length === 0 && !isFetching && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No users found</Text>
        </View>
      )}

      {showResults && results.length > 0 && (
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          keyboardShouldPersistTaps="handled"
          style={styles.resultList}
          renderItem={({ item }) => (
            <Pressable
              style={({ pressed }) => [styles.resultItem, pressed && styles.resultItemPressed]}
              onPress={() => handleSelect(item)}
            >
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>
                  {(item.full_name ?? "?").charAt(0).toUpperCase()}
                </Text>
              </View>
              <Text style={styles.resultName}>{item.full_name ?? "(no name)"}</Text>
            </Pressable>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: "100%",
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.md,
    borderWidth: 1,
    borderColor: tokens.color.border.default,
    paddingHorizontal: tokens.spacing.md,
  },
  input: {
    flex: 1,
    color: tokens.color.text.primary,
    fontSize: 16,
    paddingVertical: tokens.spacing.md,
  },
  spinner: {
    marginLeft: tokens.spacing.sm,
  },
  resultList: {
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.md,
    borderWidth: 1,
    borderColor: tokens.color.border.default,
    marginTop: 4,
    maxHeight: 240,
  },
  resultItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: tokens.spacing.md,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: tokens.color.border.subtle,
  },
  resultItemPressed: {
    backgroundColor: tokens.color.bg.surface,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: tokens.color.accent.primary,
    alignItems: "center",
    justifyContent: "center",
    marginRight: tokens.spacing.md,
  },
  avatarText: {
    color: tokens.color.white,
    fontWeight: "700",
    fontSize: 16,
  },
  resultName: {
    color: tokens.color.text.primary,
    fontSize: 15,
  },
  emptyState: {
    paddingVertical: tokens.spacing.md,
    alignItems: "center",
  },
  emptyText: {
    color: tokens.color.text.muted,
    fontSize: 14,
  },
});

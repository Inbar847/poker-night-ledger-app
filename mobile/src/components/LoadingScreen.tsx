import { StyleSheet, View } from "react-native";
import { Skeleton } from "@/components";
import { tokens } from "@/theme";

export default function LoadingScreen() {
  return (
    <View style={styles.container}>
      <Skeleton width={48} height={48} circle />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: tokens.color.bg.primary,
    alignItems: "center",
    justifyContent: "center",
  },
});

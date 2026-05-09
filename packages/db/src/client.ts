import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as {
  schluesselkinderPrisma?: PrismaClient;
};

export const prisma =
  globalForPrisma.schluesselkinderPrisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"]
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.schluesselkinderPrisma = prisma;
}

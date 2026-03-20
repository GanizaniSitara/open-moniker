-- CreateTable
CREATE TABLE "helpful_votes" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "entity_type" TEXT NOT NULL,
    "entity_key" TEXT NOT NULL,
    "helpful" BOOLEAN NOT NULL,
    "comment" TEXT,
    "author" TEXT,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateIndex
CREATE INDEX "helpful_votes_entity_type_entity_key_idx" ON "helpful_votes"("entity_type", "entity_key");

-- CreateTable
CREATE TABLE "flags" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "entity_type" TEXT NOT NULL,
    "entity_key" TEXT NOT NULL,
    "flag_type" TEXT NOT NULL,
    "comment" TEXT,
    "author" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'open',
    "resolved_by" TEXT,
    "resolved_at" DATETIME,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "suggestions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "entity_type" TEXT NOT NULL,
    "entity_key" TEXT NOT NULL,
    "field_name" TEXT NOT NULL,
    "current_value" TEXT,
    "proposed_value" TEXT NOT NULL,
    "reason" TEXT,
    "author" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "reviewed_by" TEXT,
    "review_comment" TEXT,
    "reviewed_at" DATETIME,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "annotations" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "entity_type" TEXT NOT NULL,
    "entity_key" TEXT NOT NULL,
    "annotation_type" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "author" TEXT NOT NULL,
    "upvote_count" INTEGER NOT NULL DEFAULT 0,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "annotation_votes" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "annotation_id" TEXT NOT NULL,
    "voter" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "annotation_votes_annotation_id_fkey" FOREIGN KEY ("annotation_id") REFERENCES "annotations" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "discussions" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "entity_type" TEXT NOT NULL,
    "entity_key" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "author" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "discussion_replies" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "discussion_id" TEXT NOT NULL,
    "parent_reply_id" TEXT,
    "content" TEXT NOT NULL,
    "author" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL,
    CONSTRAINT "discussion_replies_discussion_id_fkey" FOREIGN KEY ("discussion_id") REFERENCES "discussions" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "flags_entity_type_entity_key_idx" ON "flags"("entity_type", "entity_key");

-- CreateIndex
CREATE INDEX "flags_status_idx" ON "flags"("status");

-- CreateIndex
CREATE INDEX "suggestions_entity_type_entity_key_idx" ON "suggestions"("entity_type", "entity_key");

-- CreateIndex
CREATE INDEX "suggestions_status_idx" ON "suggestions"("status");

-- CreateIndex
CREATE INDEX "annotations_entity_type_entity_key_idx" ON "annotations"("entity_type", "entity_key");

-- CreateIndex
CREATE UNIQUE INDEX "annotation_votes_annotation_id_voter_key" ON "annotation_votes"("annotation_id", "voter");

-- CreateIndex
CREATE INDEX "discussions_entity_type_entity_key_idx" ON "discussions"("entity_type", "entity_key");

-- CreateIndex
CREATE INDEX "discussion_replies_discussion_id_idx" ON "discussion_replies"("discussion_id");

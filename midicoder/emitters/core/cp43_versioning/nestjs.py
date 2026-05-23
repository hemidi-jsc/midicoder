# coding: utf-8
"""
Mô-đun NestJS emitter cho Versioning & History Generator (CP43).

Emit code NestJS/TypeORM cho:
- @Versioned decorator: optimistic locking với version column
- @SoftDelete decorator: soft delete + auto filter query
- History entity: {Entity}History table với snapshot JSON
- History service: time-travel query methods
- Audit integration: auto emit audit event tới CP14

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.emitters.core.cp43_versioning.models import VersioningCollection


class NestJSVersioningEmitter:
    """
    Emitter sinh code NestJS/TypeORM cho versioning & history.

    Methods:
        generate(): Generate toàn bộ files
        generate_version_decorator(): Sinh @Versioned decorator
        generate_soft_delete_decorator(): Sinh @SoftDelete decorator
        generate_history_entity(): Sinh history entity class
        generate_history_service(): Sinh time-travel query service
        generate_audit_integration(): Sinh audit event emission (CP14)
    """

    def __init__(self, collection: VersioningCollection | None = None) -> None:
        """
        Init emitter.

        Args:
            collection: VersioningCollection (optional)
        """
        self.collection = collection or VersioningCollection()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files NestJS.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_version_decorator())
        result.update(self.generate_soft_delete_decorator())
        result.update(self.generate_history_entity())
        result.update(self.generate_history_service())
        result.update(self.generate_audit_integration())
        return result

    def generate_version_decorator(self) -> Dict[str, str]:
        """Sinh @Versioned decorator — TypeORM optimistic locking."""
        code = '''/**
 * Versioned Decorator — TypeORM decorator cho optimistic locking (CP43).
 *
 * Cung cấp:
 * - version column (Integer, default 1)
 * - Tự động increment version trước mỗi UPDATE
 * - Kiểm tra version conflict (optimistic locking)
 *
 * Sử dụng:
 *   @Entity()
 *   @Versioned()
 *   class OrderEntity {
 *     @PrimaryGeneratedColumn("uuid")
 *     id: string;
 *     // ...
 *   }
 */

import { Column } from "typeorm";

/** Target class cho decorator */
interface VersionedTarget {
  prototype: any;
  new (): any;
}

/**
 * Decorator cho optimistic locking với version column.
 *
 * Tự động thêm:
 * - version column (Integer, default 1)
 * - beforeUpdate hook để increment version
 * - checkVersion() method để validate
 */
export function Versioned(): ClassDecorator {
  return (target: VersionedTarget) => {
    const proto = target.prototype;

    // Thêm version property
    if (!proto.version) {
      Column({ type: "int", nullable: false, default: 1 })(proto, "version");
    }

    /** Kiểm tra version trước khi update (optimistic locking) */
    Object.defineProperty(proto, "checkVersion", {
      value(function (expectedVersion: number): void {
        if (this.version !== expectedVersion) {
          throw new Error(
            `Version conflict: expected v${expectedVersion}, found v${this.version}`,
          );
        }
      }),
      writable: true,
      enumerable: false,
      configurable: true,
    });

    /** Tăng version lên 1 */
    Object.defineProperty(proto, "bumpVersion", {
      value(function (): number {
        this.version = (this.version || 1) + 1;
        return this.version;
      }),
      writable: true,
      enumerable: false,
      configurable: true,
    });
  };
}

/**
 * Hook để tự động increment version trước khi update.
 *
 * Sử dụng trong entity:
 *   @BeforeUpdate()
 *   bumpVersion() {
 *     this.version = (this.version || 1) + 1;
 *   }
 */
export function BeforeUpdateVersion(): MethodDecorator {
  return (
    target: any,
    propertyKey: string | symbol,
    descriptor: PropertyDescriptor,
  ) => {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args: any[]) {
      this.version = (this.version || 1) + 1;
      return originalMethod.apply(this, args);
    };
    return descriptor;
  };
}
'''
        return {"src/common/decorators/versioned.decorator.ts": code}

    def generate_soft_delete_decorator(self) -> Dict[str, str]:
        """Sinh @SoftDelete decorator — TypeORM soft delete."""
        code = '''/**
 * SoftDelete Decorator — TypeORM decorator cho soft delete (CP43).
 *
 * Cung cấp:
 * - deletedAt column (nullable Date)
 * - deletedBy column (ký ai xóa)
 * - softDelete(): đánh dấu xóa
 * - restore(): khôi phục entity
 * - hardDelete(): xóa vĩnh viễn
 * - Auto filter: query tự động WHERE deletedAt IS NULL
 *
 * Sử dụng:
 *   @Entity()
 *   @SoftDelete()
 *   class OrderEntity {
 *     @PrimaryGeneratedColumn("uuid")
 *     id: string;
 *     // ...
 *   }
 */

import { Column, Entity, SelectQueryBuilder } from "typeorm";

/** Target class cho decorator */
interface SoftDeleteTarget {
  prototype: any;
  new (): any;
}

/**
 * Decorator cho soft delete functionality.
 *
 * Tự động thêm:
 * - deletedAt column (nullable Date, indexed)
 * - deletedBy column (nullable string)
 * - isDeleted getter
 * - softDelete(), restore(), hardDelete() methods
 */
export function SoftDelete(): ClassDecorator {
  return (target: SoftDeleteTarget) => {
    const proto = target.prototype;

    // Thêm deletedAt property
    if (!proto.deletedAt) {
      Column({ type: "timestamp", nullable: true, default: null, index: true })(proto, "deletedAt");
    }
    if (!proto.deletedBy) {
      Column({ name: "deleted_by", type: "varchar", length: 200, nullable: true, default: null })(proto, "deletedBy");
    }

    /** Kiểm tra entity có bị soft delete không */
    Object.defineProperty(proto, "isDeleted", {
      get() {
        return this.deletedAt !== null && this.deletedAt !== undefined;
      },
      enumerable: false,
      configurable: true,
    });

    /** Đánh dấu entity bị soft delete */
    Object.defineProperty(proto, "softDelete", {
      value(function (actor: string = "system"): void {
        this.deletedAt = new Date();
        this.deletedBy = actor;
      }),
      writable: true,
      enumerable: false,
      configurable: true,
    });

    /** Khôi phục entity đã bị soft delete */
    Object.defineProperty(proto, "restore", {
      value(function (): void {
        this.deletedAt = null;
        this.deletedBy = null;
      }),
      writable: true,
      enumerable: false,
      configurable: true,
    });

    /** Xóa vĩnh viễn entity */
    Object.defineProperty(proto, "hardDelete", {
      value(async function (repo: any): Promise<void> {
        await repo.remove(this);
      }),
      writable: true,
      enumerable: false,
      configurable: true,
    });
  };
}

/**
 * Tự động áp dụng filter WHERE deletedAt IS NULL cho query builder.
 *
 * Sử dụng:
 *   const query = createSoftDeletedQuery(repo.createQueryBuilder());
 *   const results = await query.getMany();
 */
export function filterSoftDeleted<T>(qb: SelectQueryBuilder<T>): SelectQueryBuilder<T> {
  return qb.andWhere(`${qb.alias}.deletedAt IS NULL`);
}
'''
        return {"src/common/decorators/soft-delete.decorator.ts": code}

    def generate_history_entity(self) -> Dict[str, str]:
        """Sinh history entity class — snapshot table."""
        code = '''/**
 * EntityHistory — Base entity cho history table (CP43).
 *
 * Mỗi entity có một history table tương ứng để lưu snapshot
 * của entity tại mỗi version. History records là IMMUTABLE.
 *
 * Sử dụng:
 *   @Entity("order_history")
 *   class OrderHistory extends EntityHistory {}
 */

import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  Index,
  CreateDateColumn,
} from "typeorm";

/** Base entity cho history table */
export abstract class EntityHistory {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @Column({ length: 200 })
  entity_id: string;

  @Column({ type: "int", default: 1 })
  version: number;

  @Column({ type: "jsonb" })
  snapshot: Record<string, any>;

  @Column({ length: 20 })
  operation: string;

  @Column({ name: "changed_fields", type: "jsonb", nullable: true })
  changed_fields: string[];

  @CreateDateColumn({ name: "created_at", type: "timestamptz" })
  created_at: Date;

  @Column({ name: "created_by", length: 200, default: "system" })
  created_by: string;

  @Column({ name: "immutable_hash", length: 64 })
  immutable_hash: string;

  /**
   * Tính SHA-256 hash cho history record (tamper-evidence).
   */
  computeHash(): string {
    const crypto = require("crypto");
    const data = {
      entity_id: this.entity_id,
      version: this.version,
      snapshot: this.snapshot,
      operation: this.operation,
      created_by: this.created_by,
      created_at: this.created_at.toISOString(),
    };
    return crypto
      .createHash("sha256")
      .update(JSON.stringify(data))
      .digest("hex");
  }
}
'''
        return {"src/common/entities/history-entity.ts": code}

    def generate_history_service(self) -> Dict[str, str]:
        """Sinh time-travel query service."""
        code = '''/**
 * HistoryService — Service cho time-travel query (CP43).
 *
 * Cung cấp các method:
 * - getAtVersion(): Lấy snapshot ở version cụ thể
 * - getAtTimestamp(): Lấy snapshot gần nhất trước thời điểm T
 * - getVersionHistory(): Lấy danh sách tất cả versions
 * - getChangesBetween(): So sánh 2 versions
 * - getLatestVersion(): Lấy version số mới nhất
 *
 * Sử dụng:
 *   const historyService = new HistoryService(historyRepo);
 *   const snapshot = await historyService.getAtVersion("order_123", 3);
 */

import { Injectable } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { Repository, LessThanOrEqual } from "typeorm";
import { EntityHistory } from "../entities/history-entity";

export interface VersionHistoryEntry {
  version: number;
  operation: string;
  snapshot: Record<string, any>;
  changed_fields: string[];
  created_at: string;
  created_by: string;
}

export interface ChangesBetween {
  old: Record<string, any> | null;
  new: Record<string, any> | null;
  changes: Array<{ field: string; old_value: any; new_value: any }>;
}

@Injectable()
export class HistoryService {
  constructor(
    @InjectRepository(EntityHistory)
    private readonly historyRepo: Repository<EntityHistory>,
  ) {}

  /**
   * Lấy snapshot của entity ở version cụ thể.
   *
   * @param entityId - ID của entity
   * @param version - Số version
   * @returns Snapshot dict hoặc null nếu không tìm thấy
   */
  async getAtVersion(
    entityId: string,
    version: number,
  ): Promise<Record<string, any> | null> {
    const record = await this.historyRepo.findOne({
      where: { entity_id: entityId, version },
    });
    return record ? record.snapshot : null;
  }

  /**
   * Lấy snapshot gần nhất trước thời điểm T.
   *
   * @param entityId - ID của entity
   * @param timestamp - Thời điểm cần query
   * @returns Snapshot dict hoặc null nếu không có record trước thời điểm T
   */
  async getAtTimestamp(
    entityId: string,
    timestamp: Date,
  ): Promise<Record<string, any> | null> {
    const record = await this.historyRepo.findOne({
      where: {
        entity_id: entityId,
        created_at: LessThanOrEqual(timestamp),
      },
      order: { created_at: "DESC" },
    });
    return record ? record.snapshot : null;
  }

  /**
   * Lấy danh sách tất cả versions của entity.
   *
   * @param entityId - ID của entity
   * @param limit - Số lượng max trả về
   * @returns List của history records
   */
  async getVersionHistory(
    entityId: string,
    limit: number = 100,
  ): Promise<VersionHistoryEntry[]> {
    const records = await this.historyRepo.find({
      where: { entity_id: entityId },
      order: { version: "DESC" },
      take: limit,
    });

    return records.map((r) => ({
      version: r.version,
      operation: r.operation,
      snapshot: r.snapshot,
      changed_fields: r.changed_fields || [],
      created_at: r.created_at.toISOString(),
      created_by: r.created_by,
    }));
  }

  /**
   * So sánh 2 versions và trả về các thay đổi.
   *
   * @param entityId - ID của entity
   * @param fromVersion - Version cũ
   * @param toVersion - Version mới
   * @returns Dict chứa snapshot cũ, mới, và các trường thay đổi
   */
  async getChangesBetween(
    entityId: string,
    fromVersion: number,
    toVersion: number,
  ): Promise<ChangesBetween> {
    const oldSnapshot = await this.getAtVersion(entityId, fromVersion);
    const newSnapshot = await this.getAtVersion(entityId, toVersion);

    if (!oldSnapshot || !newSnapshot) {
      return { old: oldSnapshot, new: newSnapshot, changes: [] };
    }

    const changes: ChangesBetween["changes"] = [];
    const allKeys = new Set([...Object.keys(oldSnapshot), ...Object.keys(newSnapshot)]);

    for (const key of allKeys) {
      const oldVal = oldSnapshot[key];
      const newVal = newSnapshot[key];
      if (oldVal !== newVal) {
        changes.push({ field: key, old_value: oldVal, new_value: newVal });
      }
    }

    return { old: oldSnapshot, new: newSnapshot, changes };
  }

  /**
   * Lấy version số mới nhất của entity.
   *
   * @param entityId - ID của entity
   * @returns Version number hoặc null nếu không có history
   */
  async getLatestVersion(entityId: string): Promise<number | null> {
    const record = await this.historyRepo.findOne({
      where: { entity_id: entityId },
      order: { version: "DESC" },
    });
    return record ? record.version : null;
  }
}
'''
        return {"src/common/services/history.service.ts": code}

    def generate_audit_integration(self) -> Dict[str, str]:
        """Sinh audit event emission — integrate với CP14."""
        code = '''/**
 * VersionAuditLogger — Auto emit audit event tới CP14 (CP43).
 *
 * Mỗi lần version thay đổi (CREATE/UPDATE/DELETE) tự động
 * emit audit event tới CP14 audit_logger.
 *
 * Sử dụng:
 *   const logger = new VersionAuditLogger(auditService);
 *   await logger.logVersionChange("Order", "order_123", "UPDATE", 1, 2, ["status"]);
 */

import { Injectable } from "@nestjs/common";
import { AuditService } from "../audit/audit.service";

export interface VersionChangeEvent {
  entity_type: string;
  entity_id: string;
  operation: string;
  old_version: number;
  new_version: number;
  changed_fields?: string[];
  user_id: string;
  tenant_id: string;
}

@Injectable()
export class VersionAuditLogger {
  /**
   * Init audit logger.
   *
   * @param auditService - CP14 AuditService (optional)
   */
  constructor(private readonly auditService?: AuditService) {}

  /**
   * Log version change event tới CP14 audit trail.
   *
   * @param params - Version change event
   */
  async logVersionChange(params: VersionChangeEvent): Promise<void> {
    if (!this.auditService) {
      return;
    }

    try {
      await this.auditService.log({
        action: params.operation,
        entity_type: params.entity_type,
        entity_id: params.entity_id,
        actor_id: params.user_id,
        actor_type: params.user_id !== "system" ? "user" : "system",
        tenant_id: params.tenant_id,
        old_values: { version: params.old_version },
        new_values: {
          version: params.new_version,
          changed_fields: params.changed_fields || [],
        },
        metadata: {
          old_version: params.old_version,
          new_version: params.new_version,
          changed_fields: params.changed_fields || [],
          operation: params.operation,
        },
      });
    } catch (error) {
      // Audit failure không nên block main operation
      console.error("Version audit log failed:", error);
    }
  }
}
'''
        return {"src/common/services/version-audit-logger.ts": code}

# coding: utf-8
"""
Mô-đun NestJS emitter cho Audit Trail & Compliance Generator (CP14).

Emit code NestJS cho audit module, service, interceptor, và entity.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict

from midicoder.packs.cp_full_audit_compliance.models import (
    AuditComplianceCollection,
)


class NestJSAuditComplianceEmitter:
    """
    Emitter sinh code NestJS cho audit trail & compliance.

    Methods:
        generate(): Generate toàn bộ files
        generate_module(): Sinh AuditModule
        generate_service(): Sinh AuditService
        generate_interceptor(): Sinh AuditInterceptor
        generate_entity(): Sinh AuditLog entity
    """

    def __init__(self, collection: AuditComplianceCollection | None = None) -> None:
        """
        Init emitter.

        Args:
            collection: AuditComplianceCollection (optional)
        """
        self.collection = collection or AuditComplianceCollection()

    def generate(self) -> Dict[str, str]:
        """
        Generate toàn bộ files NestJS.

        Returns:
            Dict {file_path: source_code}
        """
        result: Dict[str, str] = {}
        result.update(self.generate_module())
        result.update(self.generate_service())
        result.update(self.generate_interceptor())
        result.update(self.generate_entity())
        return result

    def generate_module(self) -> Dict[str, str]:
        """Sinh AuditModule."""
        code = '''/**
 * AuditModule — Module NestJS cho audit trail & compliance.
 *
 * Cung cấp:
 * - AuditService: Service quản lý audit logs
 * - AuditInterceptor: Interceptor tự động ghi audit
 */
import { Module, Global } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { AuditService } from "./audit.service";
import { AuditInterceptor } from "./audit.interceptor";
import { AuditLogEntity } from "./audit-log.entity";

@Global()
@Module({
  imports: [TypeOrmModule.forFeature([AuditLogEntity])],
  providers: [AuditService, AuditInterceptor],
  exports: [AuditService, AuditInterceptor],
})
export class AuditModule {}
'''
        return {"src/audit/audit.module.ts": code}

    def generate_service(self) -> Dict[str, str]:
        """Sinh AuditService."""
        code = '''/**
 * AuditService — Service quản lý audit trail.
 *
 * Cung cấp các method:
 * - log(): Ghi audit log entry
 * - query(): Query audit logs
 * - archive(): Archive old entries
 */
import { Injectable } from "@nestjs/common";
import { InjectRepository } from "@nestjs/typeorm";
import { Repository } from "typeorm";
import { AuditLogEntity } from "./audit-log.entity";

export interface AuditLogPayload {
  action: string;
  entity_type: string;
  entity_id: string;
  actor_id: string;
  actor_type?: string;
  tenant_id?: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  metadata?: Record<string, any>;
}

@Injectable()
export class AuditService {
  constructor(
    @InjectRepository(AuditLogEntity)
    private readonly auditRepo: Repository<AuditLogEntity>,
  ) {}

  /**
   * Ghi audit log entry.
   *
   * @param payload - Thông tin audit log
   * @returns ID của entry vừa tạo
   */
  async log(payload: AuditLogPayload): Promise<string> {
    const crypto = require("crypto");

    // Tính toán hash cho tamper-evidence
    const hashData = {
      action: payload.action,
      entity_type: payload.entity_type,
      entity_id: payload.entity_id,
      actor_id: payload.actor_id,
      actor_type: payload.actor_type || "system",
      tenant_id: payload.tenant_id || "default",
      old_values: payload.old_values || {},
      new_values: payload.new_values || {},
      metadata: payload.metadata || {},
    };
    const immutableHash = crypto
      .createHash("sha256")
      .update(JSON.stringify(hashData))
      .digest("hex");

    const entry = this.auditRepo.create({
      action: payload.action,
      entity_type: payload.entity_type,
      entity_id: payload.entity_id,
      actor_id: payload.actor_id,
      actor_type: payload.actor_type || "system",
      tenant_id: payload.tenant_id || "default",
      old_values: payload.old_values ? JSON.stringify(payload.old_values) : null,
      new_values: payload.new_values ? JSON.stringify(payload.new_values) : null,
      metadata_json: payload.metadata ? JSON.stringify(payload.metadata) : null,
      immutable_hash: immutableHash,
    });

    const saved = await this.auditRepo.save(entry);
    return saved.id;
  }

  /**
   * Query audit logs với filters.
   *
   * @param filters - Filters cho query
   * @returns List audit log entries
   */
  async query(filters: {
    entity_type?: string;
    actor_id?: string;
    tenant_id?: string;
    limit?: number;
  }): Promise<AuditLogEntity[]> {
    const where: Record<string, any> = {};
    if (filters.entity_type) where.entity_type = filters.entity_type;
    if (filters.actor_id) where.actor_id = filters.actor_id;
    if (filters.tenant_id) where.tenant_id = filters.tenant_id;

    return this.auditRepo.find({
      where,
      order: { timestamp: "DESC" },
      take: filters.limit || 100,
    });
  }

  /**
   * Archive các entries cũ hơn số ngày chỉ định.
   *
   * @param olderThanDays - Số ngày
   * @returns Số entries đã archive
   */
  async archive(olderThanDays: number): Promise<number> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);

    const result = await this.auditRepo
      .createQueryBuilder()
      .update(AuditLogEntity)
      .set({ archived: 1 })
      .where("timestamp < :cutoff", { cutoff: cutoffDate })
      .andWhere("archived = 0")
      .execute();

    return result.affected || 0;
  }
}
'''
        return {"src/audit/audit.service.ts": code}

    def generate_interceptor(self) -> Dict[str, str]:
        """Sinh AuditInterceptor."""
        code = '''/**
 * AuditInterceptor — Interceptor tự động ghi audit log.
 *
 * Interceptor này tự động ghi audit log cho các mutation methods
 * (POST, PUT, PATCH, DELETE) sau khi request thành công.
 */
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from "@nestjs/common";
import { Observable } from "rxjs";
import { tap } from "rxjs/operators";
import { Reflector } from "@nestjs/core";
import { AuditService } from "./audit.service";

@Injectable()
export class AuditInterceptor implements NestInterceptor {
  constructor(
    private readonly auditService: AuditService,
    private readonly reflector: Reflector,
  ) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const response = context.switchToHttp().getResponse();

    // Chỉ audit cho mutation methods
    const auditMethods = ["POST", "PUT", "PATCH", "DELETE"];
    const shouldAudit = auditMethods.includes(request.method);

    if (!shouldAudit) {
      return next.handle();
    }

    // Extract thông tin từ request
    const actorId = request.user?.id || "anonymous";
    const tenantId = request.tenantId || "default";
    const entityType = this.reflector.get<string>(
      "entity_type",
      context.getHandler(),
    ) || "unknown";
    const entityId = request.params?.id || request.body?.id || "unknown";

    const action = this._mapMethodToAction(request.method);

    return next.handle().pipe(
      tap(async () => {
        // Chỉ ghi audit nếu request thành công
        if (response.statusCode < 400) {
          await this.auditService.log({
            action,
            entity_type: entityType,
            entity_id: entityId,
            actor_id: actorId,
            actor_type: "user",
            tenant_id: tenantId,
            metadata: {
              ip: request.ip,
              user_agent: request.headers["user-agent"],
              url: request.url,
            },
          });
        }
      }),
    );
  }

  /**
   * Map HTTP method sang audit action.
   */
  private _mapMethodToAction(method: string): string {
    switch (method) {
      case "POST":
        return "CREATE";
      case "PUT":
      case "PATCH":
        return "UPDATE";
      case "DELETE":
        return "DELETE";
      default:
        return "READ";
    }
  }
}
'''
        return {"src/audit/audit.interceptor.ts": code}

    def generate_entity(self) -> Dict[str, str]:
        """Sinh AuditLog entity."""
        code = '''/**
 * AuditLogEntity — TypeORM entity cho audit logs.
 *
 * Lưu trữ audit log entries với immutable hash cho tamper-evidence.
 */
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  Index,
} from "typeorm";

@Entity("audit_logs")
@Index(["tenant_id"])
@Index(["entity_type", "entity_id"])
@Index(["actor_id"])
@Index(["timestamp"])
export class AuditLogEntity {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @CreateDateColumn({ type: "timestamptz" })
  timestamp: Date;

  @Column({ length: 20 })
  action: string;

  @Column({ length: 100 })
  entity_type: string;

  @Column({ length: 200 })
  entity_id: string;

  @Column({ length: 200 })
  actor_id: string;

  @Column({ length: 20, default: "system" })
  actor_type: string;

  @Column({ length: 100 })
  tenant_id: string;

  @Column({ type: "text", nullable: true })
  old_values: string | null;

  @Column({ type: "text", nullable: true })
  new_values: string | null;

  @Column({ name: "metadata_json", type: "text", nullable: true })
  metadata_json: string | null;

  @Column({ name: "immutable_hash", length: 64 })
  immutable_hash: string;

  @Column({ default: 0 })
  archived: number;
}
'''
        return {"src/audit/audit-log.entity.ts": code}
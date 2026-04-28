"""
Mô-đun NestJS Emitter cho Workflows.

Cung cấp:
- WorkflowNestJSEmitter: Generate NestJS code cho workflows

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from .models import WorkflowDefinition


class WorkflowNestJSEmitter:
    """
    Emitter cho NestJS workflows.
    
    Generate code:
    - Workflows module
    - Workflows entity
    - Workflow engine
    - Guards
    - Effects
    
    Usage:
        emitter = WorkflowNestJSEmitter()
        emitter.emit(workflows, output_path)
    """

    def emit(self, workflows: list[WorkflowDefinition], output_path: str | Path) -> list[str]:
        """
        Emit workflow code cho NestJS.
        
        Args:
            workflows: Danh sách workflow definitions
            output_path: Output directory path
            
        Returns:
            Danh sách file paths đã generate
        """
        output_path = Path(output_path)
        generated_files = []
        
        # Create output directories
        domain_path = output_path / "src" / "domain" / "workflows"
        domain_path.mkdir(parents=True, exist_ok=True)
        (domain_path / "guards").mkdir(exist_ok=True)
        (domain_path / "effects").mkdir(exist_ok=True)
        
        # Generate module
        self._emit_module(workflows, domain_path, generated_files)
        
        # Generate entity
        self._emit_entity(domain_path, generated_files)
        
        # Generate engine
        self._emit_engine(domain_path, generated_files)
        
        # Generate guards
        self._emit_guards(domain_path, generated_files)
        
        # Generate effects
        self._emit_effects(domain_path, generated_files)
        
        return generated_files

    def _emit_module(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS module."""
        content = '''import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { WorkflowEntity } from './workflows.entity';
import { WorkflowEngine } from './workflow.engine';

@Module({
    imports: [TypeOrmModule.forFeature([WorkflowEntity])],
    providers: [WorkflowEngine],
    exports: [WorkflowEngine],
})
export class WorkflowsModule {}
'''
        path = output_path / "workflows.module.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_entity(
        self,
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS entity."""
        content = '''import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity('workflow_instances')
export class WorkflowEntity {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ type: 'varchar', length: 255 })
    workflowName: string;

    @Column({ type: 'varchar', length: 255 })
    entityType: string;

    @Column({ type: 'uuid' })
    entityId: string;

    @Column({ type: 'varchar', length: 255 })
    currentState: string;

    @Column({ type: 'uuid' })
    tenantId: string;

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;
}
'''
        path = output_path / "workflows.entity.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_engine(
        self,
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS workflow engine."""
        content = '''import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { WorkflowEntity } from './workflows.entity';

export class TransitionResult {
    success: boolean;
    fromState: string;
    toState: string | null;
    transitionId: string;
    error?: string;
}

@Injectable()
export class WorkflowEngine {
    constructor(
        @InjectRepository(WorkflowEntity)
        private readonly workflowRepo: Repository<WorkflowEntity>,
    ) {}

    async transition(
        instanceId: string,
        eventName: string,
        userId?: string,
        tenantId?: string,
    ): Promise<TransitionResult> {
        // TODO: Implement transition logic
        return {
            success: false,
            fromState: '',
            toState: null,
            transitionId: '',
            error: 'Not implemented',
        };
    }

    async getState(instanceId: string): Promise<string> {
        // TODO: Implement
        return '';
    }
}
'''
        path = output_path / "workflow.engine.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_guards(
        self,
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS guards."""
        content = '''import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';

@Injectable()
export class WorkflowGuard implements CanActivate {
    canActivate(context: ExecutionContext): boolean {
        // TODO: Implement workflow guard logic
        return true;
    }
}
'''
        path = output_path / "guards" / "workflow.guard.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_effects(
        self,
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS effects."""
        content = '''import { Injectable } from '@nestjs/common';

export interface TransitionContext {
    workflowName: string;
    instanceId: string;
    entityType: string;
    entityId: string;
    fromState: string;
    toState: string;
    userId?: string;
    tenantId?: string;
}

@Injectable()
export class WorkflowEffects {
    async publishEvent(context: TransitionContext, eventName: string): Promise<void> {
        // TODO: Integrate with Event Bus
        console.log(`Published event: ${eventName}`);
    }

    async executeCommand(context: TransitionContext, commandName: string): Promise<void> {
        // TODO: Execute command
        console.log(`Executed command: ${commandName}`);
    }

    async sendNotification(
        context: TransitionContext,
        channel: string,
        template: string,
    ): Promise<void> {
        // TODO: Send notification
        console.log(`Sent notification via ${channel}: ${template}`);
    }

    async logAudit(context: TransitionContext, action: string): Promise<void> {
        // TODO: Log audit
        console.log(`Logged audit: ${action}`);
    }
}
'''
        path = output_path / "effects" / "workflow.effects.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
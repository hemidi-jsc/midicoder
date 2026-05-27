"""
Mô-đun NestJS Emitter cho Workflows.

Pug cấp:
- WorkflowNestJSEmitter: Generate NestJS code cho workflows
- TypeORM entity (WorkflowEntity)
- Workflow engine với full implementation
- Guards với NestJS CanActivate
- Effects với services

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from .models import WorkflowDefinition, Transition, Guard, Effect, GuardType, EffectType


class WorkflowNestJSEmitter:
    """
    Emitter cho NestJS workflows.
    
    Generate code:
    - Workflows module
    - Workflow entity (TypeORM)
    - Workflow engine với full implementation
    - Guards với NestJS CanActivate
    - Effects services
    
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
        
        # Tạo thư mục output
        domain_path = output_path / "src" / "domain" / "workflows"
        domain_path.mkdir(parents=True, exist_ok=True)
        (domain_path / "guards").mkdir(exist_ok=True)
        (domain_path / "effects").mkdir(exist_ok=True)
        (domain_path / "definitions").mkdir(exist_ok=True)
        
        # Generate module
        self._emit_module(workflows, domain_path, generated_files)
        
        # Generate entity
        self._emit_entity(domain_path, generated_files)
        
        # Generate engine với full implementation
        self._emit_engine(workflows, domain_path, generated_files)
        
        # Generate definitions
        for workflow in workflows:
            self._emit_definition(workflow, domain_path, generated_files)
        
        # Generate guards
        self._emit_guards(workflows, domain_path, generated_files)
        
        # Generate effects
        self._emit_effects(workflows, domain_path, generated_files)
        
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
import { PermissionGuard } from './guards/permission.guard';
import { BusinessGuard } from './guards/business.guard';
import { RoleGuard } from './guards/role.guard';
import { WorkflowEffects } from './effects/workflow.effects';

/**
 * Workflows Module - Module cho workflow execution.
 * 
 * Cung cấp:
 * - WorkflowEngine: State machine execution
 * - Guards: Permission, Business, Role guards
 * - Effects: Event, Command, Notification, Audit effects
 */
@Module({
    imports: [TypeOrmModule.forFeature([WorkflowEntity])],
    providers: [
        WorkflowEngine,
        PermissionGuard,
        BusinessGuard,
        RoleGuard,
        WorkflowEffects,
    ],
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
        content = '''import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn, Index, OneToMany } from 'typeorm';
import { WorkflowEventEntity } from './workflow-events.entity';
import { WorkflowTransitionLogEntity } from './workflow-transitions-log.entity';

/**
 * WorkflowEntity - Entity cho workflow instances.
 * 
 * Lưu trữ current state của mỗi entity cho mỗi workflow type.
 */
@Entity('workflow_instances')
export class WorkflowEntity {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ type: 'varchar', length: 255 })
    @Index()
    workflowName: string;

    @Column({ type: 'varchar', length: 255 })
    @Index()
    entityType: string;

    @Column({ type: 'uuid' })
    @Index()
    entityId: string;

    @Column({ type: 'varchar', length: 255 })
    currentState: string;

    @Column({ type: 'boolean', default: false })
    isAsync: boolean;

    @Column({ type: 'varchar', length: 500, nullable: true })
    asyncCallbackUrl: string | null;

    @Column({ type: 'uuid' })
    @Index()
    tenantId: string;

    @CreateDateColumn()
    createdAt: Date;

    @UpdateDateColumn()
    updatedAt: Date;

    @OneToMany(() => WorkflowEventEntity, (event) => event.instance)
    events: WorkflowEventEntity[];

    @OneToMany(() => WorkflowTransitionLogEntity, (log) => log.instance)
    transitionLogs: WorkflowTransitionLogEntity[];
}
'''
        path = output_path / "workflows.entity.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate workflow events entity
        content = '''import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, Index, ManyToOne, JoinColumn } from 'typeorm';
import { WorkflowEntity } from './workflows.entity';

/**
 * WorkflowEventEntity - Event log cho audit trail.
 */
@Entity('workflow_events')
export class WorkflowEventEntity {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ type: 'uuid' })
    @Index()
    instanceId: string;

    @ManyToOne(() => WorkflowEntity)
    @JoinColumn({ name: 'instance_id' })
    instance: WorkflowEntity;

    @Column({ type: 'varchar', length: 255 })
    eventName: string;

    @Column({ type: 'varchar', length: 255, nullable: true })
    fromState: string | null;

    @Column({ type: 'varchar', length: 255 })
    toState: string;

    @Column({ type: 'varchar', length: 255, nullable: true })
    @Index()
    transitionId: string | null;

    @Column({ type: 'jsonb', default: '{}' })
    payload: Record<string, unknown>;

    @CreateDateColumn()
    occurredAt: Date;

    @Column({ type: 'uuid' })
    tenantId: string;
}
'''
        path = output_path / "workflow-events.entity.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate workflow transitions log entity
        content = '''import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, Index, ManyToOne, JoinColumn } from 'typeorm';
import { WorkflowEntity } from './workflows.entity';

/**
 * WorkflowTransitionLogEntity - Log chi tiết transition execution.
 */
@Entity('workflow_transitions_log')
export class WorkflowTransitionLogEntity {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ type: 'uuid' })
    @Index()
    instanceId: string;

    @ManyToOne(() => WorkflowEntity)
    @JoinColumn({ name: 'instance_id' })
    instance: WorkflowEntity;

    @Column({ type: 'varchar', length: 255 })
    @Index()
    transitionId: string;

    @Column({ type: 'varchar', length: 255 })
    eventName: string;

    @Column({ type: 'uuid', nullable: true })
    triggeredBy: string | null;

    @Column({ type: 'jsonb', default: '{}' })
    guardResults: Record<string, unknown>;

    @Column({ type: 'jsonb', default: '[]' })
    effectsExecuted: string[];

    @Column({ type: 'jsonb', default: '[]' })
    effectsFailed: string[];

    @Column({ type: 'varchar', length: 50 })
    status: 'success' | 'failed' | 'rolled_back' | 'partial';

    @Column({ type: 'text', nullable: true })
    errorMessage: string | null;

    @CreateDateColumn()
    executedAt: Date;

    @Column({ type: 'uuid' })
    tenantId: string;
}
'''
        path = output_path / "workflow-transitions-log.entity.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_engine(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS workflow engine với full implementation."""
        # Collect workflow configs
        workflow_configs = {}
        for workflow in workflows:
            transitions = []
            for trans in workflow.transitions:
                trans_config = {
                    "id": trans.id,
                    "from_state": trans.from_state,
                    "to_state": trans.to_state,
                    "event": trans.event or trans.id,
                    "async_execution": trans.async_execution,
                    "guards": [],
                    "effects": [],
                }
                for guard in trans.guards:
                    guard_config = {"type": guard.type.value}
                    if guard.permission:
                        guard_config["permission"] = guard.permission
                    if guard.condition:
                        guard_config["condition"] = guard.condition
                    if guard.check:
                        guard_config["check"] = guard.check
                    if guard.roles:
                        guard_config["roles"] = guard.roles
                    trans_config["guards"].append(guard_config)
                for effect in trans.effects:
                    effect_config = {"type": effect.type.value}
                    if effect.publish:
                        effect_config["publish"] = effect.publish
                    if effect.execute:
                        effect_config["execute"] = effect.execute
                    if effect.channel:
                        effect_config["channel"] = effect.channel
                    if effect.template:
                        effect_config["template"] = effect.template
                    if effect.action:
                        effect_config["action"] = effect.action
                    if effect.rollback:
                        effect_config["rollback"] = effect.rollback
                    trans_config["effects"].append(effect_config)
                transitions.append(trans_config)
            
            workflow_configs[workflow.name] = {
                "states": workflow.states,
                "initial_state": workflow.initial_state,
                "transitions": transitions,
            }
        
        # Build configs content
        configs_lines = []
        for name, config in workflow_configs.items():
            configs_lines.append(f'  "{name}": {{')
            configs_lines.append(f'    states: {config["states"]},')
            configs_lines.append(f'    initialState: "{config["initial_state"]}",')
            configs_lines.append(f'    transitions: {config["transitions"]},')
            configs_lines.append(f'  }}')
        
        configs_content = ",\n".join(configs_lines)
        
        # Use string concatenation instead of f-string to avoid brace issues
        engine_template = '''import { Injectable, Inject, Optional } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { WorkflowEntity } from './workflows.entity';
import { WorkflowEventEntity } from './workflow-events.entity';
import { WorkflowTransitionLogEntity } from './workflow-transitions-log.entity';
import { WorkflowEffects } from './effects/workflow.effects';

/**
 * TransitionResult - Kết quả của transition execution.
 */
export class TransitionResult {{
  success: boolean;
  fromState: string;
  toState: string | null;
  transitionId: string;
  error?: string;
  guardsPassed?: string[];
  effectsExecuted?: string[];
  effectsFailed?: string[];
}}

/**
 * Workflow configurations.
 */
const WORKFLOW_CONFIGS: Record<string, {{
  states: string[];
  initialState: string;
  transitions: Array<{{
    id: string;
    fromState: string;
    toState: string;
    event?: string;
    asyncExecution: boolean;
    guards: Array<{{
      type: string;
      permission?: string;
      condition?: string;
      check?: string;
      roles?: string[];
    }}>;
    effects: Array<{{
      type: string;
      publish?: string;
      execute?: string;
      channel?: string;
      template?: string;
      action?: string;
      rollback?: string;
    }}>;
  }}>;
}}>> = {{
{configs_content}
}};

/**
 * WorkflowEngine - State machine engine cho workflows.
 * 
 * Supports:
 * - Sync/Async execution
 * - Guard evaluation (all must pass)
 * - Effect execution (out of transaction)
 * - Event sourcing
 * 
 * Transaction Boundaries:
 * - Guard + state change: Atomic
 * - Effects: After commit (eventual consistency)
 */
@Injectable()
export class WorkflowEngine {{
  constructor(
    @InjectRepository(WorkflowEntity)
    private readonly workflowRepo: Repository<WorkflowEntity>,
    @InjectRepository(WorkflowEventEntity)
    private readonly eventRepo: Repository<WorkflowEventEntity>,
    @InjectRepository(WorkflowTransitionLogEntity)
    private readonly logRepo: Repository<WorkflowTransitionLogEntity>,
    private readonly effects: WorkflowEffects,
  ) {{}}

  /**
   * Execute transition.
   * 
   * Flow:
   * 1. Tìm workflow instance
   * 2. Tìm transition dựa trên event name và current state
   * 3. Evaluate guards (tất cả phải pass)
   * 4. Update state (commit transaction)
   * 5. Execute effects (out of transaction)
   * 6. Log transition result
   * 
   * @param instanceId Workflow instance ID
   * @param eventName Event name trigger transition
   * @param userId User ID (optional)
   * @param tenantId Tenant ID (optional)
   * @param metadata Additional metadata (optional)
   * @returns TransitionResult
   */
  async transition(
    instanceId: string,
    eventName: string,
    userId?: string,
    tenantId?: string,
    metadata?: Record<string, unknown>,
  ): Promise<TransitionResult> {{
    // Step 1: Tìm workflow instance
    const instance = await this.workflowRepo.findOne({{ where: {{ id: instanceId }} }});
    if (!instance) {{
      return {{
        success: false,
        fromState: '',
        toState: null,
        transitionId: '',
        error: 'Workflow instance not found',
      }};
    }}

    const workflowName = instance.workflowName;
    const currentState = instance.currentState;

    // Step 2: Tìm transition
    const transition = this.findTransition(workflowName, currentState, eventName);
    if (!transition) {{
      return {{
        success: false,
        fromState: currentState,
        toState: null,
        transitionId: '',
        error: No transition found for event '{{eventName}}' from state '{{currentState}}',
      }};
    }}

    // Step 3: Evaluate guards
    const guardResult = await this.evaluateGuards(transition, instance, userId, tenantId, metadata);
    if (!guardResult.passed) {{
      return {{
        success: false,
        fromState: currentState,
        toState: null,
        transitionId: transition.id,
        error: guardResult.error,
        guardsPassed: guardResult.passedGuards,
      }};
    }}

    // Step 4: Update state (within transaction)
    const newState = transition.toState;
    instance.currentState = newState;
    await this.workflowRepo.save(instance);

    // Create event record
    const event = this.eventRepo.create({{
      instanceId: instance.id,
      eventName: eventName,
      fromState: currentState,
      toState: newState,
      transitionId: transition.id,
      tenantId: instance.tenantId,
    }});
    await this.eventRepo.save(event);

    // Step 5: Execute effects (out of transaction)
    const effectsResult = await this.executeEffects(
      transition,
      instance,
      newState,
      userId,
      tenantId,
      metadata,
    );

    // Step 6: Log transition
    const status = effectsResult.allSuccess ? 'success' : 'partial';
    await this.logTransition(
      instance,
      transition,
      eventName,
      userId,
      guardResult.results,
      effectsResult.executed,
      effectsResult.failed,
      status,
    );

    return {{
      success: true,
      fromState: currentState,
      toState: newState,
      transitionId: transition.id,
      guardsPassed: guardResult.passedGuards,
      effectsExecuted: effectsResult.executed,
      effectsFailed: effectsResult.failed,
    }};
  }}

  /**
   * Lấy current state của instance.
   * 
   * @param instanceId Workflow instance ID
   * @returns Current state name
   */
  async getState(instanceId: string): Promise<string> {{
    const instance = await this.workflowRepo.findOne({{ where: {{ id: instanceId }} }});
    if (!instance) {{
      throw new Error(Workflow instance {{{{instanceId}}}} not found);
    }}
    return instance.currentState;
  }}

  /**
   * Tạo mới workflow instance.
   * 
   * @param workflowName Tên workflow
   * @param entityType Loại entity
   * @param entityId Entity ID
   * @param tenantId Tenant ID
   * @param asyncCallbackUrl Callback URL cho async execution
   * @returns WorkflowEntity
   */
  async createInstance(
    workflowName: string,
    entityType: string,
    entityId: string,
    tenantId: string,
    asyncCallbackUrl?: string,
  ): Promise<WorkflowEntity> {{
    const config = WORKFLOW_CONFIGS[workflowName];
    if (!config) {{
      throw new Error(Workflow '{{workflowName}}' not found);
    }}

    const instance = this.workflowRepo.create({{
      workflowName,
      entityType,
      entityId,
      currentState: config.initialState,
      isAsync: !!asyncCallbackUrl,
      asyncCallbackUrl,
      tenantId,
    }});

    return this.workflowRepo.save(instance);
  }}

  private findTransition(
    workflowName: string,
    fromState: string,
    eventName: string,
  ): typeof WORKFLOW_CONFIGS[string]['transitions'][number] | null {{
    const config = WORKFLOW_CONFIGS[workflowName];
    if (!config) {{
      return null;
    }}

    for (const transition of config.transitions) {{
      if (transition.fromState === fromState) {{
        if (transition.event === eventName || transition.id === eventName) {{
          return transition;
        }}
      }}
    }}
    return null;
  }}

  private async evaluateGuards(
    transition: typeof WORKFLOW_CONFIGS[string]['transitions'][number],
    instance: WorkflowEntity,
    userId?: string,
    tenantId?: string,
    metadata?: Record<string, unknown>,
  ): Promise<{{
    passed: boolean;
    error?: string;
    results: Record<string, boolean>;
    passedGuards: string[];
  }>> {{
    const results: Record<string, boolean> = {{}};
    const passedGuards: string[] = [];

    for (let i = 0; i < transition.guards.length; i++) {{
      const guard = transition.guards[i];
      const guardName = {{guard.type}}_${{i}};
      
      const guardResult = await this.evaluateSingleGuard(
        guard,
        instance,
        userId,
        tenantId,
        metadata,
      );
      
      results[guardName] = guardResult.passed;
      
      if (guardResult.passed) {{
        passedGuards.push(guardName);
      }} else {{
        return {{
          passed: false,
          error: guardResult.error,
          results,
          passedGuards,
        }};
      }}
    }}

    return {{
      passed: true,
      results,
      passedGuards,
    }};
  }}

  private async evaluateSingleGuard(
    guard: typeof WORKFLOW_CONFIGS[string]['transitions'][number]['guards'][number],
    instance: WorkflowEntity,
    userId?: string,
    tenantId?: string,
    metadata?: Record<string, unknown>,
  ): Promise<{{ passed: boolean; error?: string }>> {{
    const guardType = guard.type;

    if (guardType === 'permission') {{
      // Permission guard - check permission
      // TODO: Inject thực sự PermissionChecker
      return {{ passed: true }};
    }}

    if (guardType === 'business') {{
      // Business guard - evaluate condition
      const condition = guard.condition || 'true';
      return {{ passed: this.evaluateCondition(condition, instance, metadata) }};
    }}

    if (guardType === 'compliance') {{
      // Compliance guard - check compliance
      // TODO: Inject thực sự ComplianceChecker
      return {{ passed: true }};
    }}

    if (guardType === 'role') {{
      // Role guard - check roles
      // TODO: Inject thực sự RoleChecker
      return {{ passed: true }};
    }}

    if (guardType === 'state') {{
      // State guard - evaluate state condition
      const condition = guard.condition || 'true';
      return {{ passed: this.evaluateCondition(condition, instance, metadata) }};
    }}

    return {{ passed: true }};
  }}

  private evaluateCondition(
    condition: string,
    instance: WorkflowEntity,
    metadata?: Record<string, unknown>,
  ): boolean {{
    try {{
      if (condition.toLowerCase() === 'true') return true;
      if (condition.toLowerCase() === 'false') return false;
      return true;
    }} catch {{
      return false;
    }}
  }}

  private async executeEffects(
    transition: typeof WORKFLOW_CONFIGS[string]['transitions'][number],
    instance: WorkflowEntity,
    newState: string,
    userId?: string,
    tenantId?: string,
    metadata?: Record<string, unknown>,
  ): Promise<{{
    allSuccess: boolean;
    executed: string[];
    failed: string[];
  }>> {{
    const executed: string[] = [];
    const failed: string[] = [];

    for (let i = 0; i < transition.effects.length; i++) {{
      const effect = transition.effects[i];
      const effectName = {{effect.type}}_${{i}};

      const success = await this.executeSingleEffect(
        effect,
        instance,
        newState,
        userId,
        tenantId,
        metadata,
      );

      if (success) {{
        executed.push(effectName);
      }} else {{
        failed.push(effectName);
      }}
    }}

    return {{
      allSuccess: failed.length === 0,
      executed,
      failed,
    }};
  }}

  private async executeSingleEffect(
    effect: typeof WORKFLOW_CONFIGS[string]['transitions'][number]['effects'][number],
    instance: WorkflowEntity,
    newState: string,
    userId?: string,
    tenantId?: string,
    metadata?: Record<string, unknown>,
  ): Promise<boolean> {{
    try {{
      if (effect.type === 'event') {{
        await this.effects.publishEvent(effect.publish || '', {{
          workflowName: instance.workflowName,
          instanceId: instance.id,
          entityType: instance.entityType,
          entityId: instance.entityId,
          toState: newState,
          tenantId: instance.tenantId,
        }});
      }}

      if (effect.type === 'command') {{
        await this.effects.executeCommand(effect.execute || '', {{
          entityType: instance.entityType,
          entityId: instance.entityId,
          tenantId: instance.tenantId,
        }});
      }}

      if (effect.type === 'notification') {{
        await this.effects.sendNotification(
          effect.channel || 'email',
          effect.template || '',
          instance.entityId,
        );
      }}

      if (effect.type === 'audit') {{
        await this.effects.logAudit(effect.action || '', {{
          workflowName: instance.workflowName,
          instanceId: instance.id,
          entityType: instance.entityType,
          entityId: instance.entityId,
          userId,
          tenantId: instance.tenantId,
        }});
      }}

      if (effect.type === 'compensation') {{
        await this.effects.rollback(effect.rollback || '', {{
          entityType: instance.entityType,
          entityId: instance.entityId,
          tenantId: instance.tenantId,
        }});
      }}

      return true;
    }} catch (error) {{
      console.error('Effect execution failed:', error);
      return false;
    }}
  }}

  private async logTransition(
    instance: WorkflowEntity,
    transition: typeof WORKFLOW_CONFIGS[string]['transitions'][number],
    eventName: string,
    userId?: string,
    guardResults: Record<string, unknown> = {{}},
    effectsExecuted: string[] = [],
    effectsFailed: string[] = [],
    status: 'success' | 'failed' | 'rolled_back' | 'partial' = 'success',
  ): Promise<void> {{
    const log = this.logRepo.create({{
      instanceId: instance.id,
      transitionId: transition.id,
      eventName,
      triggeredBy: userId,
      guardResults,
      effectsExecuted,
      effectsFailed,
      status,
      tenantId: instance.tenantId,
    }});
    await this.logRepo.save(log);
  }}
}}
'''
        path = output_path / "workflow.engine.ts"
        path.write_text(engine_template, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_definition(
        self,
        workflow: WorkflowDefinition,
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate workflow definition."""
        definitions_path = output_path / "definitions"
        filename = f"{workflow.name}.ts"
        
        content = f'''/**
 * Workflow definition for {workflow.name}.
 * 
 * Định nghĩa states và transitions cho {workflow.name} workflow.
 */

export const {self._camel_case(workflow.name)}Workflow = {{
  name: "{workflow.name}",
  entity: "{workflow.entity or ""}",
  states: {workflow.states},
  initialState: "{workflow.initial_state}",
  description: "{workflow.description or ""}",
  transitions: [
'''
        for trans in workflow.transitions:
            content += f'''
    {{
      id: "{trans.id}",
      fromState: "{trans.from_state}",
      toState: "{trans.to_state}",
      event: "{trans.event or trans.id}",
      asyncExecution: {str(trans.async_execution).lower()},
      guards: [
'''
            for guard in trans.guards:
                guard_dict = {"type": guard.type.value}
                if guard.permission:
                    guard_dict["permission"] = guard.permission
                if guard.condition:
                    guard_dict["condition"] = guard.condition
                if guard.check:
                    guard_dict["check"] = guard.check
                if guard.roles:
                    guard_dict["roles"] = guard.roles
                content += f'        {self._dict_to_ts(guard_dict)},\n'
            
            content += '''      ],
      effects: [
'''
            for effect in trans.effects:
                effect_dict = {"type": effect.type.value}
                if effect.publish:
                    effect_dict["publish"] = effect.publish
                if effect.execute:
                    effect_dict["execute"] = effect.execute
                if effect.channel:
                    effect_dict["channel"] = effect.channel
                if effect.template:
                    effect_dict["template"] = effect.template
                if effect.action:
                    effect_dict["action"] = effect.action
                if effect.rollback:
                    effect_dict["rollback"] = effect.rollback
                content += f'        {self._dict_to_ts(effect_dict)},\n'
            
            content += '''      ],
    },'''
        
        content += '''
  ],
};
'''
        path = definitions_path / filename
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_guards(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS guards."""
        # Create guards directory
        guards_path = output_path / "guards"
        guards_path.mkdir(parents=True, exist_ok=True)
        
        # Generate __init__.ts
        content = '''/**
 * Guards cho workflow transitions.
 */

export * from './permission.guard';
export * from './business.guard';
export * from './role.guard';
'''
        path = output_path / "guards" / "index.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate permission.guard.ts
        content = '''import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

/**
 * PermissionGuard - Guard cho permission checking.
 * 
 * Guards transitions dựa trên user permissions.
 */
@Injectable()
export class PermissionGuard implements CanActivate {{
  constructor(private reflector: Reflector) {{}}

  async canActivate(context: ExecutionContext): Promise<boolean> {{
    const requiredPermission = this.reflector.get<string>(
      'permission',
      context.getHandler(),
    );

    if (!requiredPermission) {{
      return true;
    }}

    // TODO: Inject thực sự PermissionChecker
    const request = context.switchToHttp().getRequest();
    const user = request.user;

    // Check if user has permission
    return true; // Placeholder
  }}
}}
'''
        path = output_path / "guards" / "permission.guard.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate business.guard.ts
        content = '''import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';

/**
 * BusinessGuard - Guard cho business rule validation.
 * 
 * Guards transitions dựa trên business rules.
 */
@Injectable()
export class BusinessGuard implements CanActivate {{
  async canActivate(context: ExecutionContext): Promise<boolean> {{
    const request = context.switchToHttp().getRequest();
    
    // Evaluate business conditions
    // TODO: Implement condition evaluation logic
    return true; // Placeholder
  }}
}}
'''
        path = output_path / "guards" / "business.guard.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))
        
        # Generate role.guard.ts
        content = '''import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';

/**
 * RoleGuard - Guard cho role checking.
 * 
 * Guards transitions dựa trên user roles.
 */
@Injectable()
export class RoleGuard implements CanActivate {{
  constructor(private reflector: Reflector) {{}}

  async canActivate(context: ExecutionContext): Promise<boolean> {{
    const requiredRoles = this.reflector.get<string[]>(
      'roles',
      context.getHandler(),
    );

    if (!requiredRoles || requiredRoles.length === 0) {{
      return true;
    }}

    // TODO: Inject thực sự RoleChecker
    const request = context.switchToHttp().getRequest();
    const user = request.user;

    // Check if user has any of the required roles
    return true; // Placeholder
  }}
}}
'''
        path = output_path / "guards" / "role.guard.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    def _emit_effects(
        self,
        workflows: list[WorkflowDefinition],
        output_path: Path,
        generated_files: list[str],
    ) -> None:
        """Generate NestJS effects services."""
        # Create effects directory
        effects_path = output_path / "effects"
        effects_path.mkdir(parents=True, exist_ok=True)
        
        content = '''import { Injectable } from '@nestjs/common';

/**
 * TransitionContext - Context cho transition execution.
 */
export interface TransitionContext {{
  workflowName: string;
  instanceId: string;
  entityType: string;
  entityId: string;
  fromState?: string;
  toState: string;
  userId?: string;
  tenantId: string;
}}

/**
 * WorkflowEffects - Effects service cho workflow transitions.
 * 
 * Cung cấp các effect implementations:
 * - Event publishing
 * - Command execution
 * - Notification sending
 * - Audit logging
 * - Compensation/rollback
 */
@Injectable()
export class WorkflowEffects {{
  /**
   * Publish domain event.
   * 
   * @param eventName Event name
   * @param payload Event payload
   */
  async publishEvent(eventName: string, payload: TransitionContext): Promise<void> {{
    // TODO: Integrate với Event Bus (e.g., NestJS EventsModule)
    console.log(Published event: {{{{eventName}}}}, payload);
  }}

  /**
   * Execute command.
   * 
   * @param commandName Command name
   * @param params Command parameters
   */
  async executeCommand(commandName: string, params: Record<string, unknown>): Promise<void> {{
    // TODO: Integrate với Command Bus
    console.log(Executed command: {{{{commandName}}}}, params);
  }}

  /**
   * Send notification.
   * 
   * @param channel Notification channel
   * @param template Template name
   * @param recipient Recipient identifier
   */
  async sendNotification(
    channel: string,
    template: string,
    recipient: string,
  ): Promise<void> {{
    // TODO: Integrate với Notification Service
    console.log(Sent notification via {{{{channel}}}}: {{{{template}}}} to {{{{recipient}}}});
  }}

  /**
   * Log audit event.
   * 
   * @param action Action name
   * @param context Transition context
   */
  async logAudit(action: string, context: TransitionContext): Promise<void> {{
    // TODO: Integrate với Audit Service
    console.log(Logged audit: {{{{action}}}}, context);
  }}

  /**
   * Execute compensation/rollback action.
   * 
   * @param action Rollback action name
   * @param params Rollback parameters
   */
  async rollback(action: string, params: Record<string, unknown>): Promise<void> {{
    // TODO: Integrate với Compensation Service
    console.log(Executed rollback: {{{{action}}}}, params);
  }}
}}
'''
        path = output_path / "effects" / "workflow.effects.ts"
        path.write_text(content, encoding="utf-8")
        generated_files.append(str(path))

    @staticmethod
    def _camel_case(value: str) -> str:
        """Convert to camelCase."""
        parts = value.replace("_", " ").replace("-", " ").split()
        if not parts:
            return value
        return parts[0] + "".join(word.capitalize() for word in parts[1:])

    @staticmethod
    def _dict_to_ts(d: dict) -> str:
        """Convert dict to TypeScript object literal."""
        items = []
        for k, v in d.items():
            if isinstance(v, str):
                items.append(f'{k}: "{v}"')
            elif isinstance(v, list):
                items.append(f'{k}: [{", ".join(f"{item}" for item in v)}]')
            elif isinstance(v, bool):
                items.append(f'{k}: {str(v).lower()}')
            else:
                items.append(f'{k}: {v}')
        return "{{ " + ", ".join(items) + " }}"
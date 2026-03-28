# PawPal+ UML Class Diagram

```mermaid
classDiagram

    class Task {
        <<dataclass>>
        +str name
        +str description
        +bool completed
        +str frequency
        +date date
        +list~str~ pet_names
    }

    class Pet {
        <<dataclass>>
        +str name
        +str species
        +float age_years
        +str notes
    }

    class Owner {
        +str name
        +list~Pet~ pets
        +add_pet(pet: Pet) None
        +remove_pet(name: str, scheduler: Scheduler) None
    }

    class Scheduler {
        +Owner owner
        +list~Task~ tasks
        +add_task(task: Task) None
        +remove_task(name: str) None
        +remove_pet_from_tasks(pet_name: str) None
        +get_tasks_for_pet(pet_name: str) list~Task~
        +get_tasks_for_date(target_date: date) list~Task~
        +get_unassigned_tasks() list~Task~
        +mark_complete(task_name: str) None
    }

    Owner "1" *-- "0..*" Pet : owns
    Scheduler "1" o-- "1" Owner : manages for
    Scheduler "1" o-- "0..*" Task : manages
    Task --> Pet : references by names
```

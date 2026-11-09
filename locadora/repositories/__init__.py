"""Repositórios: o único lugar do projeto que escreve SQL.

Cada módulo cuida de UMA tabela:

- ``carros``   -> locadora_carro
- ``clientes`` -> locadora_perfilcliente (+ auth_user para nome/username)
- ``alugueis`` -> locadora_aluguel
- ``multas``   -> locadora_multa

Services chamam os repositórios; views nunca escrevem SQL.

Desenvolvido com orientação do Prof. Henry (ver docs/padroes-de-codigo.md).
"""

# -*- coding: utf-8


class SimpleHansaTransaction(object):
    """
    Hansa row-export transaction
    """
    def __init__(self, txn_id, year, entry_date, txn_date, txn_title, txn_ref, rows):
        """
        :param txn_id: Hansa transaction identifier, e.g. 123
        :param year: Transaction year, e.g. 2013
        :param entry_date: Entry date, e.g. 01.02.2015
        :param txn_date: Transaction date, must match transaction year
        :param txn_title: Short free-form title for the transaction
        :param txn_ref: External transaction reference number, e.g. lentotili
        :param rows: Transaction rows
        :type txn_id: int
        :type year: int
        :type entry_date: string
        :type txn_date: string
        :type txn_title: string
        :type txn_ref: string
        :type rows: list of SimpleHansaRow objects
        """
        self.txn_id = txn_id
        self.year = year
        self.entry_date = entry_date
        self.txn_date = txn_date
        self.txn_title = txn_title
        self.txn_ref = txn_ref
        self.rows = rows

    def hansaformat(self):
        out = []
        def cur(amount):
            if amount is None:
                return ""
            else:
                return ("%.2f" %amount).replace(".", ",")
        for row in self.rows:
            TXN = "%d\t%d\t%s\t%s\t%s\t%s" %(self.txn_id, self.year, self.entry_date, self.txn_title, self.txn_date, self.txn_ref)
            ROW = "\t%d\t\t%s\t\t\t%s\t%s\t\t\t\t\t" %(row.account_no, row.row_title, cur(row.debit), cur(row.credit))
            out.append(TXN + ROW)
        return "\r\n".join(out) + "\r\n"

class SimpleHansaRow(object):
    """
    One row in Hansa import format
    """
    def __init__(self, account_no, row_title, debit=None, credit=None):
        """
        :param account_no: Hansa account number
        :param row_title: Short row title
        :param debit: Debit amount
        :parma credit: Credit amount
        :type account_no: int
        :type row_title: string
        :type debit: float
        :type credit: float
        """
        self.account_no = account_no
        self.row_title = row_title
        if not ((debit is None) ^ (credit is None)):
            raise ValueError("Must have either credit or debit but not both: %d, %s, credit: %s, debit: %s" %(account_no, row_title, credit, debit))
        
        self.debit = debit
        self.credit = credit

    def __str__(self):
        if self.credit is not None:
            return "HansaRow(%d, %s, credit=%.2f)" % (self.account_no, self.row_title, self.credit)
        else:
            return "HansaRow(%d, %s, debit=%.2f)" % (self.account_no, self.row_title, self.debit)

    def __cmp__(self, other):
        return cmp((self.account_no, self.row_title, self.debit, self.credit), (other.account_no, other.row_title, other.debit, other.credit))

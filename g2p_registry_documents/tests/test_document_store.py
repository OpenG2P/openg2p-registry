import base64

from odoo.addons.component.tests.common import TransactionComponentCase


class TestG2PDocumentStoreRegistry(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.registrant = self.env["res.partner"].create({"name": "Test Registrant"})
        self.backend = self.env["storage.backend"].create(
            {
                "name": "Test Document Store",
            }
        )

    def test_adding_file_for_registrant(self):
        """Test adding a file for a registrant"""

        data = b"Test data1"
        document1 = self.backend.add_file_registrant(data, name="test.txt", registrant=self.registrant)
        self.assertTrue(document1.registrant_id)

        # Retesting with existing document
        data = b"Test data2"
        document2 = self.backend.add_file_registrant(data, name="test.txt", registrant=self.registrant)
        self.assertTrue(document2.registrant_id, self.registrant)

    def test_registrant_supporting_documents(self):
        """Test adding supporting documents directry to res.partner"""

        data = b"Test data3"
        encoded_data = base64.b64encode(data).decode("utf-8")
        partner = self.env["res.partner"].create(
            {
                "name": "Test Registrant 2",
                "supporting_documents_ids": [
                    (
                        0,
                        0,
                        {"name": "Document 1", "backend_id": self.backend.id, "data": encoded_data},
                    )
                ],
            }
        )

        self.assertEqual(partner.supporting_documents_ids[0].registrant_id, partner)
        partner_supporting_document_data_str = partner.supporting_documents_ids[0].data.decode("utf-8")
        self.assertEqual(partner_supporting_document_data_str, encoded_data)

        # add another document
        data = b"Test data4"
        encoded_data = base64.b64encode(data).decode("utf-8")
        partner.supporting_documents_ids = [
            (
                0,
                0,
                {"name": "Document 2", "backend_id": self.backend.id, "data": encoded_data},
            )
        ]

        self.assertEqual(partner.supporting_documents_ids[1].registrant_id, partner)
        partner_supporting_document_data_str = partner.supporting_documents_ids[1].data.decode("utf-8")
        self.assertEqual(partner_supporting_document_data_str, encoded_data)

    def test_deleting_supporting_documents(self):
        """Test deleting supporting documents from partner"""

        data = b"Test data5"
        encoded_data = base64.b64encode(data).decode("utf-8")
        partner = self.env["res.partner"].create(
            {
                "name": "Test Registrant 3",
                "supporting_documents_ids": [
                    (
                        0,
                        0,
                        {"name": "Document 3", "backend_id": self.backend.id, "data": encoded_data},
                    )
                ],
            }
        )

        self.assertEqual(len(partner.supporting_documents_ids), 1)

        # Now, delete the supporting document
        partner.supporting_documents_ids.unlink()

        # Verify that the supporting documents are deleted
        self.assertEqual(len(partner.supporting_documents_ids), 0)

    def test_adding_multiple_supporting_documents(self):
        """Test adding multiple supporting documents to a partner"""

        data1 = b"Test data6"
        data2 = b"Test data7"
        encoded_data1 = base64.b64encode(data1).decode("utf-8")
        encoded_data2 = base64.b64encode(data2).decode("utf-8")
        partner = self.env["res.partner"].create(
            {
                "name": "Test Registrant 4",
                "supporting_documents_ids": [
                    (
                        0,
                        0,
                        {"name": "Document 4-1", "backend_id": self.backend.id, "data": encoded_data1},
                    ),
                    (
                        0,
                        0,
                        {"name": "Document 4-2", "backend_id": self.backend.id, "data": encoded_data2},
                    ),
                ],
            }
        )

        self.assertEqual(len(partner.supporting_documents_ids), 2)
        self.assertEqual(partner.supporting_documents_ids[0].registrant_id, partner)
        self.assertEqual(partner.supporting_documents_ids[1].registrant_id, partner)
        self.assertEqual(partner.supporting_documents_ids[0].data.decode("utf-8"), encoded_data1)
        self.assertEqual(partner.supporting_documents_ids[1].data.decode("utf-8"), encoded_data2)

    def test_updating_supporting_documents(self):
        """Test updating documents of a partner"""

        data = b"Test data8"
        encoded_data = base64.b64encode(data).decode("utf-8")
        partner = self.env["res.partner"].create(
            {
                "name": "Test Registrant 5",
                "supporting_documents_ids": [
                    (
                        0,
                        0,
                        {"name": "Document 5", "backend_id": self.backend.id, "data": encoded_data},
                    )
                ],
            }
        )

        new_name = "Document 5 - Updated"
        partner.supporting_documents_ids[0].write({"name": new_name})

        self.assertEqual(partner.supporting_documents_ids[0].name, new_name)
